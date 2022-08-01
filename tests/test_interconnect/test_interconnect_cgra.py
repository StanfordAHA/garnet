import tempfile
import os
from gemstone.common.testers import BasicTester
from canal.util import IOSide
import lassen.asm as asm
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


@pytest.mark.parametrize("batch_size", [100])
def test_interconnect_point_wise(batch_size: int, run_tb, io_sides):
    # we test a simple point-wise multiplier function
    # to account for different CGRA size, we feed in data to the very top-left
    # SB and route through horizontally to reach very top-right SB
    # we configure the top-left PE as multiplier
    chip_size = 2
    interconnect = create_cgra(chip_size, chip_size, io_sides,
                               num_tracks=3,
                               add_pd=True,
                               mem_ratio=(1, 2))

    netlist = {
        "e0": [("I0", "io2f_16"), ("p0", "data0")],
        "e1": [("I1", "io2f_16"), ("p0", "data1")],
        "e3": [("p0", "res"), ("I2", "f2io_16")],
    }
    bus = {"e0": 16, "e1": 16, "e3": 16}

    placement, routing, _ = pnr(interconnect, (netlist, bus))
    config_data = interconnect.get_route_bitstream(routing)

    x, y = placement["p0"]
    tile = interconnect.tile_circuits[(x, y)]
    add_bs = tile.core.get_config_bitstream(asm.umult0())
    for addr, data in add_bs:
        config_data.append((interconnect.get_config_addr(addr, 0, x, y), data))
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

    src0 = placement["I0"]
    src1 = placement["I1"]
    src_name0 = interconnect.get_top_input_port_by_coord(src0, 16)
    src_name1 = interconnect.get_top_input_port_by_coord(src1, 16)
    dst = placement["I2"]
    dst_name = interconnect.get_top_output_port_by_coord(dst, 16)
    random.seed(0)
    for _ in range(batch_size):
        num_1 = random.randrange(0, 256)
        num_2 = random.randrange(0, 256)
        tester.poke(circuit.interface[src_name0], num_1)
        tester.poke(circuit.interface[src_name1], num_2)

        tester.eval()
        tester.expect(circuit.interface[dst_name], num_1 * num_2)

    run_tb(tester)


def test_interconnect_sram(run_tb, io_sides):

    # NEW: PASSES

    # WHAT CHANGED HERE? MOVING FROM GENESIS TO KRATOS
    # Basically same
    chip_size = 2
    interconnect = create_cgra(chip_size, chip_size, io_sides,
                               num_tracks=3,
                               add_pd=True,
                               mem_ratio=(1, 2))

    # In this case, we use the write address for both addresses
    addr_in_0 = ONYX_PORT_REMAP['RAM']['wr_addr_in_0']
    data_out_0 = ONYX_PORT_REMAP['RAM']['data_out_0']
    ren_in_0 = ONYX_PORT_REMAP['RAM']['ren_in_0']

    netlist = {
        "e0": [("I0", "io2f_16"), ("m0", addr_in_0)],
        "e1": [("m0", data_out_0), ("I1", "f2io_16")],
        "e2": [("i3", "io2f_1"), ("m0", ren_in_0)]
    }
    bus = {"e0": 16, "e1": 16, "e2": 1}

    placement, routing, _ = pnr(interconnect, (netlist, bus))
    config_data = interconnect.get_route_bitstream(routing)

    mode = 2  # Mode.SRAM
    tile_en = 1
    configs_mem = [("mode", mode, 0),
                   ("tile_en", tile_en, 0)]
    mem_x, mem_y = placement["m0"]
    memtile = interconnect.tile_circuits[(mem_x, mem_y)]
    mcore = memtile.core
    config_mem_tile(interconnect, config_data, configs_mem, mem_x, mem_y, mcore)
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

    addr_coord = placement["I0"]
    src = interconnect.get_top_input_port_by_coord(addr_coord, 16)
    dst_coord = placement["I1"]
    dst = interconnect.get_top_output_port_by_coord(dst_coord, 16)
    ren_coord = placement["i3"]
    ren = interconnect.get_top_input_port_by_coord(ren_coord, 1)

    tester.step(2)
    tester.poke(circuit.interface[ren], 1)
    tester.eval()

    for i in range(2048):
        tester.poke(circuit.interface[src], i)
        tester.eval()
        tester.step(2)
        tester.eval()
        tester.expect(circuit.interface[dst], i)

    run_tb(tester)


@pytest.mark.parametrize("depth", [10, 1024])
def test_interconnect_fifo(run_tb, io_sides, depth):

    # NEW: PASSES

    # WHAT CHANGED HERE? MOVING FROM GENESIS TO KRATOS
    # Basically same

    chip_size = 2
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
        "e0": [("I0", "io2f_16"), ("m0", data_in_0)],
        "e1": [("i3", "io2f_1"), ("m0", wen_in_0)],
        "e2": [("i4", "io2f_1"), ("m0", ren_in_0)],
        "e3": [("m0", data_out_0), ("I1", "f2io_16")],
        "e4": [("m0", valid_out_0), ("i4", "f2io_1")],
        "e5": [("m0", empty_p), ("i2", "f2io_1")],
        "e6": [("m0", full_p), ("i3", "f2io_1")]
    }
    bus = {"e0": 16, "e1": 1, "e2": 1, "e3": 16, "e4": 1, "e5": 1, "e6": 1}

    placement, routing, _ = pnr(interconnect, (netlist, bus))
    config_data = interconnect.get_route_bitstream(routing)

    configs_mem = [("mem_ctrl_strg_fifo_flat_strg_fifo_inst_fifo_depth", depth, 0),
                   ("mode", 1, 0),
                   ("tile_en", 1, 0)]

    mem_x, mem_y = placement["m0"]
    memtile = interconnect.tile_circuits[(mem_x, mem_y)]
    mcore = memtile.core
    config_mem_tile(interconnect, config_data, configs_mem, mem_x, mem_y, mcore)
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

    src_coord = placement["I0"]
    src = interconnect.get_top_input_port_by_coord(src_coord, 16)
    dst_coord = placement["I1"]
    dst = interconnect.get_top_output_port_by_coord(dst_coord, 16)
    wen_coord = placement["i3"]
    wen = interconnect.get_top_input_port_by_coord(wen_coord, 1)
    valid_coord = placement["i4"]
    valid = interconnect.get_top_output_port_by_coord(valid_coord, 1)
    ren_coord = placement["i4"]
    ren = interconnect.get_top_input_port_by_coord(ren_coord, 1)
    full_coord = placement["i3"]
    full = interconnect.get_top_output_port_by_coord(full_coord, 1)
    empty_coord = placement["i2"]
    empty = interconnect.get_top_output_port_by_coord(empty_coord, 1)

    tester.step(1)

    fifo = deque()
    valid_check = 0
    most_recent_read = 0
    for i in range(2048):

        len_fifo = len(fifo)

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
            write_val = random.randint(0, 60000)
            tester.poke(circuit.interface[wen], 1)
            tester.poke(circuit.interface[src], write_val)
            if (len(fifo) < depth):
                fifo.appendleft(write_val)
            valid_check = 0
        elif move == 2:
            # r and w
            write_val = random.randint(0, 60000)
            tester.poke(circuit.interface[wen], 1)
            tester.poke(circuit.interface[ren], 1)
            tester.poke(circuit.interface[src], write_val)
            fifo.appendleft(write_val)
            most_recent_read = fifo.pop()
            valid_check = 1
        else:
            # If not doing anything, valid will be low, and we expect
            # to see the same output as before
            valid_check = 0
        tester.eval()

        tester.expect(circuit.interface[empty], len_fifo == 0)
        tester.expect(circuit.interface[full], len_fifo == depth)
        tester.expect(circuit.interface[valid], valid_check)
        if valid_check:
            tester.expect(circuit.interface[dst], most_recent_read)
        tester.step(2)

        tester.poke(circuit.interface[wen], 0)
        tester.poke(circuit.interface[ren], 0)

    run_tb(tester)
