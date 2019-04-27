import tempfile
import glob
import shutil
import os
from gemstone.common.testers import BasicTester
from canal.global_signal import apply_global_meso_wiring
from canal.interconnect import Interconnect
from canal.util import create_uniform_interconnect, SwitchBoxType, IOSide
from memory_core.memory_core_magma import MemCore
from peak_core.peak_core import PeakCore
from lassen.sim import gen_pe
import lassen.asm as asm
from canal.cyclone import SwitchBoxSide, SwitchBoxIO
from io_core.io_core_magma import IOCore
from archipelago import pnr
import pytest
import random
from power_domain.pd_pass import add_power_domain
import magma


@pytest.fixture(scope="module")
def cw_files():
    filenames = ["CW_fp_add.v", "CW_fp_mult.v"]
    dirname = "peak_core"
    result_filenames = []
    for name in filenames:
        filename = os.path.join(dirname, name)
        assert os.path.isfile(filename)
        result_filenames.append(filename)
    return result_filenames


@pytest.mark.parametrize("batch_size", [100])
@pytest.mark.parametrize("add_pd", [True, False])
def test_interconnect_point_wise(batch_size: int, cw_files, add_pd):
    # we test a simple point-wise multiplier function
    # to account for different CGRA size, we feed in data to the very top-left
    # SB and route through horizontally to reach very top-right SB
    # we configure the top-left PE as multiplier
    chip_size = 2
    interconnect = create_cgra(chip_size, add_io=True, add_pd=add_pd)

    netlist = {
        "e0": [("I0", "io2f_16"), ("p0", "data0")],
        "e1": [("I1", "io2f_16"), ("p0", "data1")],
        "e3": [("p0", "alu_res"), ("I2", "f2io_16")],
    }
    bus = {"e0": 16, "e1": 16, "e3": 16}

    placement, routing = pnr(interconnect, (netlist, bus))
    config_data = interconnect.get_route_bitstream(routing)

    x, y = placement["p0"]
    tile_id = x << 8 | y
    tile = interconnect.tile_circuits[(x, y)]
    add_bs = tile.core.configure(asm.umult0())
    for addr, data in add_bs:
        config_data.append(((addr << 24) | tile_id, data))

    circuit = interconnect.circuit()

    tester = BasicTester(circuit, circuit.clk, circuit.reset)
    tester.reset()
    # set the PE core
    for addr, index in config_data:
        tester.configure(addr, index)
        tester.config_read(addr)
        tester.eval()
        tester.expect(circuit.read_config_data, index)

    src_x0, src_y0 = placement["I0"]
    src_x1, src_y1 = placement["I1"]
    src_name0 = f"glb2io_16_X{src_x0}_Y{src_y0}"
    src_name1 = f"glb2io_16_X{src_x1}_Y{src_y1}"
    dst_x, dst_y = placement["I2"]
    dst_name = f"io2glb_16_X{dst_x}_Y{dst_y}"
    random.seed(0)
    for _ in range(batch_size):
        num_1 = random.randrange(0, 256)
        num_2 = random.randrange(0, 256)
        tester.poke(circuit.interface[src_name0], num_1)
        tester.poke(circuit.interface[src_name1], num_2)

        tester.eval()
        tester.expect(circuit.interface[dst_name], num_1 * num_2)

    with tempfile.TemporaryDirectory() as tempdir:
        for genesis_verilog in glob.glob("genesis_verif/*.*"):
            shutil.copy(genesis_verilog, tempdir)
        for filename in cw_files:
            shutil.copy(filename, tempdir)
        shutil.copy(os.path.join("tests", "test_memory_core",
                                 "sram_stub.v"),
                    os.path.join(tempdir, "sram_512w_16b.v"))
        tester.compile_and_run(target="verilator",
                               magma_output="coreir-verilog",
                               directory=tempdir,
                               flags=["-Wno-fatal", "--trace"])


@pytest.mark.parametrize("add_pd", [False])
def test_interconnect_line_buffer(cw_files, add_pd):
    chip_size = 2
    depth = 10
    interconnect = create_cgra(chip_size, add_io=True, add_pd=add_pd)

    netlist = {
        "e0": [("I0", "io2f_16"), ("m0", "data_in"), ("p0", "data0")],
        "e1": [("m0", "data_out"), ("p0", "data1")],
        "e3": [("p0", "alu_res"), ("I1", "f2io_16")],
        "e4": [("I0", "io2f_1"), ("m0", "wen_in")]
    }
    bus = {"e0": 16, "e1": 16, "e3": 16, "e4": 1}

    placement, routing = pnr(interconnect, (netlist, bus), cwd="tmp")
    config_data = interconnect.get_route_bitstream(routing)

    # in this case we configure m0 as line buffer mode
    mem_x, mem_y = placement["m0"]
    config_data.append((0x00000000 | (mem_x << 8 | mem_y),
                        0x00000004 | (depth << 3)))
    # then p0 is configured as add
    pe_x, pe_y = placement["p0"]
    tile_id = pe_x << 8 | pe_y
    tile = interconnect.tile_circuits[(pe_x, pe_y)]

    add_bs = tile.core.configure(asm.add())
    for addr, data in add_bs:
        config_data.append(((addr << 24) | tile_id, data))

    circuit = interconnect.circuit()

    tester = BasicTester(circuit, circuit.clk, circuit.reset)
    tester.reset()
    for addr, index in config_data:
        tester.configure(addr, index)
        tester.config_read(addr)
        tester.eval()
        tester.expect(circuit.read_config_data, index)

    src_x, src_y = placement["I0"]
    src = f"glb2io_16_X{src_x}_Y{src_y}"
    dst_x, dst_y = placement["I1"]
    dst = f"io2glb_16_X{dst_x}_Y{dst_y}"
    wen_x, wen_y = placement["I0"]
    wen = f"glb2io_1_X{wen_x}_Y{wen_y}"

    tester.poke(circuit.interface[wen], 1)

    for i in range(200):
        tester.poke(circuit.interface[src], i)
        tester.eval()

        if i > depth + 10:
            tester.expect(circuit.interface[dst], i * 2 - depth)

        # toggle the clock
        tester.step(2)

    with tempfile.TemporaryDirectory() as tempdir:
        for genesis_verilog in glob.glob("genesis_verif/*.*"):
            shutil.copy(genesis_verilog, tempdir)
        for filename in cw_files:
            shutil.copy(filename, tempdir)
        shutil.copy(os.path.join("tests", "test_memory_core",
                                 "sram_stub.v"),
                    os.path.join(tempdir, "sram_512w_16b.v"))
        tester.compile_and_run(target="verilator",
                               magma_output="coreir-verilog",
                               directory=tempdir,
                               flags=["-Wno-fatal"])


@pytest.mark.parametrize("add_pd", [True, False])
def test_interconnect_sram(cw_files, add_pd):
    chip_size = 2
    interconnect = create_cgra(chip_size, add_io=True, add_pd=add_pd)

    netlist = {
        "e0": [("I0", "io2f_16"), ("m0", "addr_in")],
        "e1": [("m0", "data_out"), ("I1", "f2io_16")],
        "e2": [("I0", "io2f_1"), ("m0", "ren_in")]
    }
    bus = {"e0": 16, "e1": 16, "e2": 1}

    placement, routing = pnr(interconnect, (netlist, bus))
    config_data = interconnect.get_route_bitstream(routing)

    x, y = placement["m0"]
    sram_config_addr = 0x00000000 | (x << 8 | y)
    # in this case we configure (1, 0) as sram mode
    config_data.append((sram_config_addr, 0x00000006))

    sram_data = []
    # add SRAM data
    for i in range(0, 1024, 4):
        feat_addr = i // 256 + 1
        mem_addr = i % 256
        sram_data.append((sram_config_addr | mem_addr << 24 | feat_addr << 16,
                          i + 10))

    circuit = interconnect.circuit()

    tester = BasicTester(circuit, circuit.clk, circuit.reset)
    tester.reset()
    for addr, index in config_data:
        tester.configure(addr, index)
        tester.config_read(addr)
        tester.eval()
        tester.expect(circuit.read_config_data, index)

    for addr, data in sram_data:
        tester.configure(addr, data)
        # currently read back doesn't work
        # tester.config_read(addr)
        # tester.eval()
        # tester.expect(circuit.read_config_data, data)

    addr_x, addr_y = placement["I0"]
    src = f"glb2io_16_X{addr_x}_Y{addr_y}"
    dst_x, dst_y = placement["I1"]
    dst = f"io2glb_16_X{dst_x}_Y{dst_y}"
    ren_x, ren_y = placement["I0"]
    ren = f"glb2io_1_X{ren_x}_Y{ren_y}"

    tester.step(2)
    tester.poke(circuit.interface[ren], 1)
    tester.eval()

    for i in range(0, 1024, 4):
        tester.poke(circuit.interface[src], i)
        tester.eval()
        tester.step(2)
        tester.eval()
        tester.expect(circuit.interface[dst], i + 10)

    with tempfile.TemporaryDirectory() as tempdir:
        for genesis_verilog in glob.glob("genesis_verif/*.*"):
            shutil.copy(genesis_verilog, tempdir)
        for filename in cw_files:
            shutil.copy(filename, tempdir)
        shutil.copy(os.path.join("tests", "test_memory_core",
                                 "sram_stub.v"),
                    os.path.join(tempdir, "sram_512w_16b.v"))
        tester.compile_and_run(target="verilator",
                               magma_output="coreir-verilog",
                               directory=tempdir,
                               flags=["-Wno-fatal"])


def create_cgra(chip_size: int, add_io: bool = False,
                num_tracks: int = 3,
                add_pd: bool = True):
    # currently only add 16bit io cores
    reg_mode = True
    addr_width = 8
    data_width = 32
    bit_widths = [1, 16]
    tile_id_width = 16
    track_length = 1
    margin = 0 if not add_io else 1
    sides = (IOSide.North | IOSide.East | IOSide.South | IOSide.West) \
        if add_io else IOSide.None_
    chip_size += 2 * margin
    # recalculate the margin
    # creates all the cores here
    # we don't want duplicated cores when snapping into different interconnect
    # graphs
    cores = {}
    for x in range(chip_size):
        for y in range(chip_size):
            # empty corner
            if x in range(margin) and y in range(margin):
                core = None
            elif x in range(margin) and y in range(chip_size - margin,
                                                   chip_size):
                core = None
            elif x in range(chip_size - margin,
                            chip_size) and y in range(margin):
                core = None
            elif x in range(chip_size - margin,
                            chip_size) and y in range(chip_size - margin,
                                                      chip_size):
                core = None
            elif x in range(margin) \
                    or x in range(chip_size - margin, chip_size) \
                    or y in range(margin) \
                    or y in range(chip_size - margin, chip_size):
                core = IOCore()
            else:
                core = MemCore(16, 1024) if ((x - margin) % 2 == 1) else \
                    PeakCore(gen_pe)
            cores[(x, y)] = core

    def create_core(xx: int, yy: int):
        return cores[(xx, yy)]

    # specify input and output port connections
    inputs = ["data0", "data1", "bit0", "bit1", "bit2", "data_in",
              "addr_in", "flush", "ren_in", "wen_in", "clk_en"]
    outputs = ["alu_res", "alu_res_p", "data_out"]
    # this is slightly different from the chip we tape out
    # here we connect input to every SB_IN and output to every SB_OUT
    port_conns = {}
    in_conn = []
    out_conn = []
    for side in SwitchBoxSide:
        in_conn.append((side, SwitchBoxIO.SB_IN))
        out_conn.append((side, SwitchBoxIO.SB_OUT))
    for input_port in inputs:
        port_conns[input_port] = in_conn
    for output_port in outputs:
        port_conns[output_port] = out_conn
    pipeline_regs = []
    for track in range(num_tracks):
        for side in SwitchBoxSide:
            pipeline_regs.append((track, side))
    # if reg mode is off, reset to empty
    if not reg_mode:
        pipeline_regs = []
    ics = {}

    io_in = {"f2io_1": [1], "f2io_16": [0]}
    io_out = {"io2f_1": [1], "io2f_16": [0]}
    for bit_width in bit_widths:
        if add_io:
            io_conn = {"in": io_in, "out": io_out}
        else:
            io_conn = None
        ic = create_uniform_interconnect(chip_size, chip_size, bit_width,
                                         create_core,
                                         port_conns,
                                         {track_length: num_tracks},
                                         SwitchBoxType.Disjoint,
                                         pipeline_regs,
                                         io_sides=sides,
                                         io_conn=io_conn)
        ics[bit_width] = ic

    lift_ports = margin == 0
    interconnect = Interconnect(ics, addr_width, data_width, tile_id_width,
                                lift_ports=lift_ports)
    if add_pd:
        add_power_domain(interconnect)
    interconnect.finalize()
    apply_global_meso_wiring(interconnect, io_sides=sides)
    return interconnect
