import tempfile
import os
from gemstone.common.testers import BasicTester
from canal.util import IOSide
import lassen.asm as asm
from lassen.sim import PE_fc as lassen_fc
from peak.assembler import Assembler
from hwtypes.modifiers import strip_modifiers
from archipelago import pnr
import pytest
import random
from cgra import create_cgra, compress_config_data
import magma
from memory_core.memory_core_magma import config_mem_tile
from collections import deque
from memory_core.memtile_util import ONYX_PORT_REMAP


@pytest.fixture()
def io_sides():
    return IOSide.North | IOSide.East | IOSide.South | IOSide.West


def test_1x1():
    # this is all PE
    interconnect = create_cgra(1, 1, IOSide.None_, num_tracks=3, mem_ratio=(0, 1))
    circuit = interconnect.circuit()
    with tempfile.TemporaryDirectory() as temp:
        filename = os.path.join(temp, "1x1")
        magma.compile(filename, circuit, inline=False)
        assert os.path.isfile(filename + ".v")


@pytest.mark.skip(reason="04/2023 skip for clean master branch, see garnet issue 924")
@pytest.mark.parametrize("batch_size", [100])
def test_interconnect_point_wise(batch_size: int, run_tb, io_sides, get_mapping):
    # we test a simple point-wise multiplier function
    # to account for different CGRA size, we feed in data to the very top-left
    # SB and route through horizontally to reach very top-right SB
    # we configure the top-left PE as multiplier
    chip_size = 2
    interconnect = create_cgra(chip_size, chip_size, io_sides,
                               num_tracks=3,
                               add_pd=True,
                               mem_ratio=(1, 2))

    pe_map, mem_map = get_mapping(interconnect)
    pe_map = pe_map["alu"]

    netlist = {
        "e0": [("I0", "io2f_17"), ("p0", pe_map["data0"])],
        "e1": [("I1", "io2f_17"), ("p0", pe_map["data1"])],
        "e3": [("p0", pe_map["res"]), ("I2", "f2io_17")],
    }
    bus = {"e0": 17, "e1": 17, "e3": 17}

    placement, routing, _ = pnr(interconnect, (netlist, bus))
    config_data = interconnect.get_route_bitstream(routing)

    x, y = placement["p0"]
    tile = interconnect.tile_circuits[(x, y)]
    instr_type = strip_modifiers(lassen_fc.Py.input_t.field_dict['inst'])
    asm_ = Assembler(instr_type)
    pe_bs = asm_.assemble(asm.umult0())
    add_bs = tile.core.get_config_bitstream(pe_bs)
    for addr, data in add_bs:
        config_data.append((interconnect.get_config_addr(addr, 0, x, y), data))

    src0 = placement["I0"]
    src1 = placement["I1"]
    dst = placement["I2"]

    # Need to configure IO tiles, empty instr since dense case is fixed
    instr = {}

    for place in [src0, src1, dst]:
        iotile = interconnect.tile_circuits[place]
        value = iotile.core.get_config_bitstream(instr)
        for addr, data in value:
            config_data.append((interconnect.get_config_addr(addr, 0, place[0], place[1]), data))

    config_data = compress_config_data(config_data)

    circuit = interconnect.circuit()

    tester = BasicTester(circuit, circuit.clk, circuit.reset)
    tester.zero_inputs()
    tester.reset()
    # set the PE core
    for addr, index in config_data:
        tester.configure(addr, index)
        tester.config_read(addr)
        tester.eval()
        tester.expect(circuit.read_config_data, index)
        # insert one dummy cycle for the new debugging read
        tester.done_config()
        tester.eval()

    tester.done_config()

    src_name0 = interconnect.get_top_input_port_by_coord(src0, 17)
    src_name1 = interconnect.get_top_input_port_by_coord(src1, 17)
    dst_name = interconnect.get_top_output_port_by_coord(dst, 17)
    random.seed(0)
    for _ in range(batch_size):
        num_1 = random.randrange(0, 256)
        num_2 = random.randrange(0, 256)
        tester.poke(circuit.interface[src_name0], num_1)
        tester.poke(circuit.interface[src_name1], num_2)
        tester.eval()
        tester.step(4)
        tester.expect(circuit.interface[dst_name], num_1 * num_2)

    run_tb(tester, include_PE=True)


@pytest.mark.skip(reason="04/2023 skip for clean master branch, see garnet issue 924")
def test_interconnect_sram(run_tb, io_sides, get_mapping):
    # NEW: PASSES

    # WHAT CHANGED HERE? MOVING FROM GENESIS TO KRATOS
    # Basically same
    # TODO I don't think mem_ratio is working correctly here
    chip_size = 4
    interconnect = create_cgra(chip_size, chip_size, io_sides,
                               num_tracks=3,
                               add_pd=True,
                               mem_ratio=(1, 2))

    pe_map, mem_map = get_mapping(interconnect)
    pe_map = pe_map["alu"]

    # In this case, we use the write address for both addresses
    # in ROM mode, only the wr_addr_in is used
    netlist = {
        "e0": [("I0", "io2f_17"), ("m0", mem_map["ROM"]["wr_addr_in"])],
        "e1": [("m0", mem_map["ROM"]["data_out"]), ("I1", "f2io_17")],
        "e2": [("i3", "io2f_1"), ("m0", mem_map["ROM"]["ren"])]
    }
    bus = {"e0": 17, "e1": 17, "e2": 1}

    placement, routing, _ = pnr(interconnect, (netlist, bus))
    config_data = interconnect.get_route_bitstream(routing)

    mode = 4  # Mode.SRAM
    tile_en = 1
    configs_mem = [("mode", mode, 0),
                   ("tile_en", tile_en, 0)]
    mem_x, mem_y = placement["m0"]
    memtile = interconnect.tile_circuits[(mem_x, mem_y)]
    mcore = memtile.core
    config_mem_tile(interconnect, config_data, configs_mem, mem_x, mem_y, mcore)

    addr_coord = placement["I0"]
    dst_coord = placement["I1"]
    ren_coord = placement["i3"]

    # Configure IO
    instr = {}

    for place in [addr_coord, dst_coord, ren_coord]:
        iotile = interconnect.tile_circuits[place]
        value = iotile.core.get_config_bitstream(instr)
        for addr, data in value:
            config_data.append((interconnect.get_config_addr(addr, 0, place[0], place[1]), data))

    config_data = compress_config_data(config_data)

    # in this case we configure (1, 0) as sram mode
    sram_data = []
    # add SRAM data
    for i in range(0, 512):
        feat_addr = i // 256 + 1
        mem_addr = i % 256
        sram_data.append((interconnect.get_config_addr(mem_addr, feat_addr,
                                                       mem_x, mem_y),
                          i))

    circuit = interconnect.circuit()

    tester = BasicTester(circuit, circuit.clk, circuit.reset)
    tester.zero_inputs()
    tester.reset()
    for addr, index in config_data:
        tester.configure(addr, index)
        tester.config_read(addr)
        tester.eval()
        tester.expect(circuit.read_config_data, index)
        # insert one dummy cycle for the new debugging read
        tester.done_config()
        tester.eval()

    for addr, data in sram_data:
        for i in range(4):
            tester.configure(addr, data * 4 + i)
            tester.eval()
        # currently read back doesn't work
        for i in range(4):
            tester.config_read(addr)
            tester.eval()
            tester.expect(circuit.read_config_data, data * 4 + i)
            # insert one dummy cycle for the new debugging read
            tester.done_config()
            tester.eval()

    for addr, index in config_data:
        tester.configure(addr, index)
        tester.config_read(addr)
        tester.eval()
        tester.expect(circuit.read_config_data, index)
        # insert one dummy cycle for the new debugging read
        tester.done_config()
        tester.eval()

    tester.done_config()

    src = interconnect.get_top_input_port_by_coord(addr_coord, 17)
    dst = interconnect.get_top_output_port_by_coord(dst_coord, 17)
    ren = interconnect.get_top_input_port_by_coord(ren_coord, 1)

    tester.step(2)
    tester.poke(circuit.interface[ren], 1)
    tester.eval()

    for i in range(2050):
        tester.poke(circuit.interface[src], i)
        tester.eval()
        tester.step(2)
        tester.eval()
        if i >= 2:
            tester.expect(circuit.interface[dst], i - 2)

    run_tb(tester, include_PE=True)


@pytest.mark.skip
@pytest.mark.skip
@pytest.mark.parametrize("depth", [10, 1024])
def test_interconnect_fifo(run_tb, io_sides, depth):

    # NEW: PASSES

    # WHAT CHANGED HERE? MOVING FROM GENESIS TO KRATOS
    # Basically same

    chip_size = 4
    interconnect = create_cgra(chip_size, chip_size, io_sides,
                               num_tracks=3,
                               add_pd=True,
                               mem_ratio=(1, 2))

    data_in_0 = ONYX_PORT_REMAP['FIFO']['data_in_0']
    wen_in_0 = ONYX_PORT_REMAP['FIFO']['wen_in_0']
    ren_in_0 = ONYX_PORT_REMAP['FIFO']['ren_in_0']
    data_out_0 = ONYX_PORT_REMAP['FIFO']['data_out_0']
    valid_out_0 = ONYX_PORT_REMAP['FIFO']['valid_out_0']
    empty_p = ONYX_PORT_REMAP['FIFO']['empty']
    full_p = ONYX_PORT_REMAP['FIFO']['full']

    netlist = {
        "e0": [("I0", "io2f_17"), ("m0", data_in_0)],
        "e1": [("i3", "io2f_1"), ("m0", wen_in_0)],
        "e2": [("i4", "io2f_1"), ("m0", ren_in_0)],
        "e3": [("m0", data_out_0), ("I1", "f2io_17")],
        "e4": [("m0", valid_out_0), ("i4", "f2io_1")],
        "e5": [("m0", empty_p), ("i2", "f2io_1")],
        "e6": [("m0", full_p), ("i3", "f2io_1")]
    }
    bus = {"e0": 17, "e1": 1, "e2": 1, "e3": 17, "e4": 1, "e5": 1, "e6": 1}

    placement, routing, _ = pnr(interconnect, (netlist, bus))
    config_data = interconnect.get_route_bitstream(routing)

    configs_mem = [("mem_ctrl_strg_fifo_flat_strg_fifo_inst_fifo_depth", depth, 0),
                   ("mode", 1, 0),
                   ("tile_en", 1, 0)]

    mem_x, mem_y = placement["m0"]
    memtile = interconnect.tile_circuits[(mem_x, mem_y)]
    mcore = memtile.core
    config_mem_tile(interconnect, config_data, configs_mem, mem_x, mem_y, mcore)

    src_coord = placement["I0"]
    dst_coord = placement["I1"]
    wen_coord = placement["i3"]
    valid_coord = placement["i4"]
    ren_coord = placement["i4"]
    full_coord = placement["i3"]
    empty_coord = placement["i2"]

    # default io configuration
    instr = {}
    for place in [src_coord, dst_coord, wen_coord, valid_coord, ren_coord, full_coord, empty_coord]:
        iotile = interconnect.tile_circuits[place]
        value = iotile.core.get_config_bitstream(instr)
        for addr, data in value:
            config_data.append((interconnect.get_config_addr(addr, 0, place[0], place[1]), data))

    config_data = compress_config_data(config_data)

    circuit = interconnect.circuit()

    tester = BasicTester(circuit, circuit.clk, circuit.reset)
    tester.zero_inputs()
    tester.reset()
    for addr, index in config_data:
        tester.configure(addr, index)
        tester.config_read(addr)
        tester.eval()
        tester.expect(circuit.read_config_data, index)
        # insert one dummy cycle for the new debugging read
        tester.done_config()
        tester.eval()

    src = interconnect.get_top_input_port_by_coord(src_coord, 17)
    dst = interconnect.get_top_output_port_by_coord(dst_coord, 17)
    wen = interconnect.get_top_input_port_by_coord(wen_coord, 1)
    valid = interconnect.get_top_output_port_by_coord(valid_coord, 1)
    ren = interconnect.get_top_input_port_by_coord(ren_coord, 1)
    full = interconnect.get_top_output_port_by_coord(full_coord, 1)
    empty = interconnect.get_top_output_port_by_coord(empty_coord, 1)

    tester.step(1)

    fifo = deque()
    valid_check = 0
    for i in range(2048):

        len_fifo = len(fifo)
        write_val = random.randint(0, 60000)
        passthru = False

        # Pick random from (READ, WRITE, READ_AND_WRITE)
        move = random.randint(0, 3)
        if move == 0:
            # read
            tester.poke(circuit.interface[ren], 1)
            if (len(fifo) > 0):
                most_recent_read = fifo.pop()
                # tester.expect(circuit.interface[dst], most_recent_read)
                valid_check = 1
            else:
                valid_check = 0
        elif move == 1:
            # write
            tester.poke(circuit.interface[wen], 1)
            tester.poke(circuit.interface[src], write_val)

            if (len(fifo) < depth):
                fifo.appendleft(write_val)
            valid_check = 0
        elif move == 2:
            # r and w
            tester.poke(circuit.interface[wen], 1)
            tester.poke(circuit.interface[ren], 1)
            tester.poke(circuit.interface[src], write_val)
            # We support a passthru mode, so we need to handle that case
            if len_fifo == 0:
                fifo.appendleft(write_val)
                passthru = True
            valid_check = 1
        else:
            # If not doing anything, valid will be low, and we expect
            # to see the same output as before
            valid_check = len_fifo > 0

        top_val = 0
        if len(fifo) > 0:
            top_val = fifo[len(fifo) - 1]

        tester.eval()

        tester.expect(circuit.interface[empty], len_fifo == 0)
        tester.expect(circuit.interface[full], len_fifo == depth)
        tester.expect(circuit.interface[valid], valid_check)
        if valid_check:
            tester.expect(circuit.interface[dst], top_val)
        tester.step(2)

        if move == 0:
            # read
            if (len(fifo) > 0):
                fifo.pop()
        elif move == 1:
            # write
            if (len(fifo) < depth):
                fifo.appendleft(write_val)
        elif move == 2:
            # r and w
            if passthru is False:
                fifo.appendleft(write_val)
            fifo.pop()

        tester.poke(circuit.interface[wen], 0)
        tester.poke(circuit.interface[ren], 0)

    run_tb(tester)
