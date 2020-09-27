import tempfile
import math
import glob
import shutil
import os
from gemstone.common.testers import BasicTester
from canal.util import IOSide
import lassen.asm as asm
from archipelago import pnr
import pytest
import random
from cgra import create_cgra, compress_config_data
from memory_core.memory_mode import Mode
from memory_core.memory_core_magma import config_mem_tile
from collections import deque


@pytest.fixture()
def io_sides():
    return IOSide.North | IOSide.East | IOSide.South | IOSide.West


@pytest.fixture(scope="module")
def dw_files():
    filenames = ["DW_fp_add.v", "DW_fp_mult.v"]
    dirname = "peak_core"
    result_filenames = []
    for name in filenames:
        filename = os.path.join(dirname, name)
        assert os.path.isfile(filename)
        result_filenames.append(filename)
    return result_filenames


@pytest.mark.parametrize("batch_size", [100])
def test_interconnect_point_wise(batch_size: int, dw_files, io_sides):
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
        "e3": [("p0", "alu_res"), ("I2", "f2io_16")],
    }
    bus = {"e0": 16, "e1": 16, "e3": 16}

    placement, routing = pnr(interconnect, (netlist, bus))
    config_data = interconnect.get_route_bitstream(routing)

    x, y = placement["p0"]
    tile = interconnect.tile_circuits[(x, y)]
    add_bs = tile.core.get_config_bitstream(asm.umult0())
    for addr, data in add_bs:
        config_data.append((interconnect.get_config_addr(addr, 0, x, y), data))
    config_data = compress_config_data(config_data)

    circuit = interconnect.circuit()

    tester = BasicTester(circuit, circuit.clk, circuit.reset)
    tester.circuit.clk = 0
    tester.reset()
    # set the PE core
    for addr, index in config_data:
        tester.configure(addr, index)
        tester.config_read(addr)
        tester.eval()
        tester.expect(circuit.read_config_data, index)

    tester.done_config()

    src_x0, src_y0 = placement["I0"]
    src_x1, src_y1 = placement["I1"]
    src_name0 = f"glb2io_16_X{src_x0:02X}_Y{src_y0:02X}"
    src_name1 = f"glb2io_16_X{src_x1:02X}_Y{src_y1:02X}"
    dst_x, dst_y = placement["I2"]
    dst_name = f"io2glb_16_X{dst_x:02X}_Y{dst_y:02X}"
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
        for filename in dw_files:
            shutil.copy(filename, tempdir)
        shutil.copy(os.path.join("tests", "test_memory_core",
                                 "sram_stub.v"),
                    os.path.join(tempdir, "sram_512w_16b.v"))
        for aoi_mux in glob.glob("tests/*.sv"):
            shutil.copy(aoi_mux, tempdir)
        tester.compile_and_run(target="verilator",
                               magma_output="coreir-verilog",
                               magma_opts={"coreir_libs": {"float_DW"}},
                               directory=tempdir,
                               flags=["-Wno-fatal"])


def test_interconnect_sram(dw_files, io_sides):

    # NEW: PASSES

    # WHAT CHANGED HERE? MOVING FROM GENESIS TO KRATOS
    # Basically same
    chip_size = 2
    interconnect = create_cgra(chip_size, chip_size, io_sides,
                               num_tracks=3,
                               add_pd=True,
                               mem_ratio=(1, 2))

    netlist = {
        "e0": [("I0", "io2f_16"), ("m0", "addr_in_0")],
        "e1": [("m0", "data_out_0"), ("I1", "f2io_16")],
        "e2": [("i3", "io2f_1"), ("m0", "ren_in_0")]
    }
    bus = {"e0": 16, "e1": 16, "e2": 1}

    placement, routing = pnr(interconnect, (netlist, bus))
    config_data = interconnect.get_route_bitstream(routing)

    mode = 2  # Mode.SRAM
    tile_en = 1
    configs_mem = [("mode", mode, 0),
                   ("tile_en", tile_en, 0),
                   ("flush_reg_sel", 1, 0)]
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
    tester.reset()
    for addr, index in config_data:
        tester.configure(addr, index)
        tester.config_read(addr)
        tester.eval()
        tester.expect(circuit.read_config_data, index)

    for addr, data in sram_data:
        for i in range(4):
            tester.configure(addr, data * 4 + i)
            tester.eval()
        # currently read back doesn't work
        for i in range(4):
            tester.config_read(addr)
            tester.eval()
            tester.expect(circuit.read_config_data, data * 4 + i)

    for addr, index in config_data:
        tester.configure(addr, index)
        tester.config_read(addr)
        tester.eval()
        tester.expect(circuit.read_config_data, index)

    tester.done_config()

    addr_x, addr_y = placement["I0"]
    src = f"glb2io_16_X{addr_x:02X}_Y{addr_y:02X}"
    dst_x, dst_y = placement["I1"]
    dst = f"io2glb_16_X{dst_x:02X}_Y{dst_y:02X}"
    ren_x, ren_y = placement["i3"]
    ren = f"glb2io_1_X{ren_x:02X}_Y{ren_y:02X}"

    tester.step(2)
    tester.poke(circuit.interface[ren], 1)
    tester.eval()

    for i in range(2048):
        tester.poke(circuit.interface[src], i)
        tester.eval()
        tester.step(2)
        tester.eval()
        tester.expect(circuit.interface[dst], i)

    with tempfile.TemporaryDirectory() as tempdir:
        for genesis_verilog in glob.glob("genesis_verif/*.*"):
            shutil.copy(genesis_verilog, tempdir)
        for filename in dw_files:
            shutil.copy(filename, tempdir)
        shutil.copy(os.path.join("tests", "test_memory_core",
                                 "sram_stub.v"),
                    os.path.join(tempdir, "sram_512w_16b.v"))
        for aoi_mux in glob.glob("tests/*.sv"):
            shutil.copy(aoi_mux, tempdir)
        tester.compile_and_run(target="verilator",
                               magma_output="coreir-verilog",
                               magma_opts={"coreir_libs": {"float_DW"}},
                               directory=tempdir,
                               flags=["-Wno-fatal"])


@pytest.mark.parametrize("depth", [10, 1024])
def test_interconnect_fifo(dw_files, io_sides, depth):

    # NEW: PASSES

    # WHAT CHANGED HERE? MOVING FROM GENESIS TO KRATOS
    # Basically same

    chip_size = 2
    interconnect = create_cgra(chip_size, chip_size, io_sides,
                               num_tracks=3,
                               add_pd=True,
                               mem_ratio=(1, 2))

    netlist = {
        "e0": [("I0", "io2f_16"), ("m0", "data_in_0")],
        "e1": [("i3", "io2f_1"), ("m0", "wen_in_0")],
        "e2": [("i4", "io2f_1"), ("m0", "ren_in_0")],
        "e3": [("m0", "data_out_0"), ("I1", "f2io_16")],
        "e4": [("m0", "valid_out_0"), ("i4", "f2io_1")],
        "e5": [("m0", "empty"), ("i2", "f2io_1")],
        "e6": [("m0", "full"), ("i3", "f2io_1")]
    }
    bus = {"e0": 16, "e1": 1, "e2": 1, "e3": 16, "e4": 1, "e5": 1, "e6": 1}

    placement, routing = pnr(interconnect, (netlist, bus))
    config_data = interconnect.get_route_bitstream(routing)

    # in this case we configure m0 as fifo mode
    mode = 1  # Mode.FIFO
    tile_en = 1

    almost_count = 3
    if(depth < 5):
        almost_count = 0

    configs_mem = [("fifo_ctrl_fifo_depth", depth, 0),
                   ("mode", 1, 0),
                   ("tile_en", tile_en, 0),
                   ("flush_reg_sel", 1, 0)]
    mem_x, mem_y = placement["m0"]
    memtile = interconnect.tile_circuits[(mem_x, mem_y)]
    mcore = memtile.core
    config_mem_tile(interconnect, config_data, configs_mem, mem_x, mem_y, mcore)
    config_data = compress_config_data(config_data)

    circuit = interconnect.circuit()

    tester = BasicTester(circuit, circuit.clk, circuit.reset)
    tester.reset()
    for addr, index in config_data:
        tester.configure(addr, index)
        tester.config_read(addr)
        tester.eval()
        tester.expect(circuit.read_config_data, index)

    src_x, src_y = placement["I0"]
    src = f"glb2io_16_X{src_x:02X}_Y{src_y:02X}"
    dst_x, dst_y = placement["I1"]
    dst = f"io2glb_16_X{dst_x:02X}_Y{dst_y:02X}"
    wen_x, wen_y = placement["i3"]
    wen = f"glb2io_1_X{wen_x:02X}_Y{wen_y:02X}"
    valid_x, valid_y = placement["i4"]
    valid = f"io2glb_1_X{valid_x:02X}_Y{valid_y:02X}"
    ren_x, ren_y = placement["i4"]
    ren = f"glb2io_1_X{ren_x:02X}_Y{ren_y:02X}"
    full_x, full_y = placement["i3"]
    full = f"io2glb_1_X{full_x:02X}_Y{full_y:02X}"
    empty_x, empty_y = placement["i2"]
    empty = f"io2glb_1_X{empty_x:02X}_Y{empty_y:02X}"

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
            if(len(fifo) > 0):
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
            if(len(fifo) < depth):
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

    with tempfile.TemporaryDirectory() as tempdir:
        for genesis_verilog in glob.glob("genesis_verif/*.*"):
            shutil.copy(genesis_verilog, tempdir)
        for filename in dw_files:
            shutil.copy(filename, tempdir)
        shutil.copy(os.path.join("tests", "test_memory_core",
                                 "sram_stub.v"),
                    os.path.join(tempdir, "sram_512w_16b.v"))
        for aoi_mux in glob.glob("tests/*.sv"):
            shutil.copy(aoi_mux, tempdir)
        tester.compile_and_run(target="verilator",
                               magma_output="coreir-verilog",
                               magma_opts={"coreir_libs": {"float_DW"}},
                               directory=tempdir,
                               flags=["-Wno-fatal"])
