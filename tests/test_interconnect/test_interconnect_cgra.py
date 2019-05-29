import tempfile
import glob
import shutil
import os
from gemstone.common.testers import BasicTester
from canal.util import IOSide
import lassen.asm as asm
from archipelago import pnr
import pytest
import random
from cgra import create_cgra
from memory_core.memory_core import Mode


@pytest.fixture()
def io_sides():
    return IOSide.North | IOSide.East | IOSide.South | IOSide.West


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
def test_interconnect_point_wise(batch_size: int, cw_files, add_pd, io_sides):
    # we test a simple point-wise multiplier function
    # to account for different CGRA size, we feed in data to the very top-left
    # SB and route through horizontally to reach very top-right SB
    # we configure the top-left PE as multiplier
    chip_size = 2
    interconnect = create_cgra(chip_size, chip_size, io_sides,
                               num_tracks=3,
                               add_pd=add_pd,
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
        for filename in cw_files:
            shutil.copy(filename, tempdir)
        shutil.copy(os.path.join("tests", "test_memory_core",
                                 "sram_stub.v"),
                    os.path.join(tempdir, "sram_512w_16b.v"))
        for aoi_mux in glob.glob("tests/*.sv"):
            shutil.copy(aoi_mux, tempdir)
        tester.compile_and_run(target="verilator",
                               magma_output="coreir-verilog",
                               directory=tempdir,
                               flags=["-Wno-fatal"])


@pytest.mark.parametrize("add_pd", [True, False])
@pytest.mark.parametrize("depth", [10, 100])
@pytest.mark.parametrize("stencil_width", [3, 5])
def test_interconnect_line_buffer_last_line_valid(cw_files, add_pd, io_sides,
                                                  stencil_width, depth):

    chip_size = 2
    interconnect = create_cgra(chip_size, chip_size, io_sides,
                               num_tracks=3,
                               add_pd=add_pd,
                               mem_ratio=(1, 2))

    netlist = {
        "e0": [("I0", "io2f_16"), ("m0", "data_in"), ("p0", "data0")],
        "e1": [("m0", "data_out"), ("p0", "data1")],
        "e3": [("p0", "alu_res"), ("I1", "f2io_16")],
        "e4": [("i3", "io2f_1"), ("m0", "wen_in")],
        "e5": [("m0", "valid_out"), ("i4", "f2io_1")]
    }
    bus = {"e0": 16, "e1": 16, "e3": 16, "e4": 1, "e5": 1}

    placement, routing = pnr(interconnect, (netlist, bus))
    config_data = interconnect.get_route_bitstream(routing)

    # in this case we configure m0 as line buffer mode

    mode = Mode.LINE_BUFFER
    tile_en = 1

    mem_x, mem_y = placement["m0"]
    memtile = interconnect.tile_circuits[(mem_x, mem_y)]
    mcore = memtile.core
    config_data.append((interconnect.get_config_addr(
                        mcore.get_reg_index("depth"),
                        0, mem_x, mem_y), depth))
    config_data.append((interconnect.get_config_addr(
                        mcore.get_reg_index("mode"),
                        0, mem_x, mem_y), mode.value))
    config_data.append((interconnect.get_config_addr(
                        mcore.get_reg_index("stencil_width"),
                        0, mem_x, mem_y), stencil_width))
    config_data.append((interconnect.get_config_addr(
                        mcore.get_reg_index("tile_en"),
                        0, mem_x, mem_y), tile_en))

    # then p0 is configured as add
    pe_x, pe_y = placement["p0"]
    tile_id = pe_x << 8 | pe_y
    tile = interconnect.tile_circuits[(pe_x, pe_y)]

    add_bs = tile.core.get_config_bitstream(asm.add())
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
    src = f"glb2io_16_X{src_x:02X}_Y{src_y:02X}"
    dst_x, dst_y = placement["I1"]
    dst = f"io2glb_16_X{dst_x:02X}_Y{dst_y:02X}"
    wen_x, wen_y = placement["i3"]
    wen = f"glb2io_1_X{wen_x:02X}_Y{wen_y:02X}"
    valid_x, valid_y = placement["i4"]
    valid = f"io2glb_1_X{valid_x:02X}_Y{valid_y:02X}"

    tester.poke(circuit.interface[wen], 1)

    counter = 0
    for i in range(3 * depth):
        tester.poke(circuit.interface[src], counter)
        tester.eval()

        if i < depth + stencil_width - 1:
            tester.expect(circuit.interface[valid], 0)
        elif i < 2 * depth:
            tester.expect(circuit.interface[valid], 1)
        elif i < 2 * depth + stencil_width - 1:
            tester.expect(circuit.interface[valid], 0)
        else:
            tester.expect(circuit.interface[valid], 1)

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
        for aoi_mux in glob.glob("tests/*.sv"):
            shutil.copy(aoi_mux, tempdir)
        tester.compile_and_run(target="verilator",
                               magma_output="coreir-verilog",
                               directory=tempdir,
                               flags=["-Wno-fatal", "--trace"])


@pytest.mark.parametrize("add_pd", [True, False])
def test_interconnect_line_buffer(cw_files, add_pd, io_sides):
    depth = 10
    chip_size = 2
    interconnect = create_cgra(chip_size, chip_size, io_sides,
                               num_tracks=3,
                               add_pd=add_pd,
                               mem_ratio=(1, 2))

    netlist = {
        "e0": [("I0", "io2f_16"), ("m0", "data_in"), ("p0", "data0")],
        "e1": [("m0", "data_out"), ("p0", "data1")],
        "e3": [("p0", "alu_res"), ("I1", "f2io_16")],
        "e4": [("i3", "io2f_1"), ("m0", "wen_in")],
        "e5": [("m0", "valid_out"), ("i4", "f2io_1")]
    }
    bus = {"e0": 16, "e1": 16, "e3": 16, "e4": 1, "e5": 1}

    placement, routing = pnr(interconnect, (netlist, bus))
    config_data = interconnect.get_route_bitstream(routing)

    # in this case we configure m0 as line buffer mode

    mode = Mode.LINE_BUFFER
    tile_en = 1

    mem_x, mem_y = placement["m0"]
    memtile = interconnect.tile_circuits[(mem_x, mem_y)]
    mcore = memtile.core
    config_data.append((interconnect.get_config_addr(
                        mcore.get_reg_index("depth"),
                        0, mem_x, mem_y), depth))
    config_data.append((interconnect.get_config_addr(
                        mcore.get_reg_index("mode"),
                        0, mem_x, mem_y), mode.value))
    config_data.append((interconnect.get_config_addr(
                        mcore.get_reg_index("tile_en"),
                        0, mem_x, mem_y), tile_en))

    # then p0 is configured as add
    pe_x, pe_y = placement["p0"]
    tile_id = pe_x << 8 | pe_y
    tile = interconnect.tile_circuits[(pe_x, pe_y)]

    add_bs = tile.core.get_config_bitstream(asm.add())
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
    src = f"glb2io_16_X{src_x:02X}_Y{src_y:02X}"
    dst_x, dst_y = placement["I1"]
    dst = f"io2glb_16_X{dst_x:02X}_Y{dst_y:02X}"
    wen_x, wen_y = placement["i3"]
    wen = f"glb2io_1_X{wen_x:02X}_Y{wen_y:02X}"
    valid_x, valid_y = placement["i4"]
    valid = f"io2glb_1_X{valid_x:02X}_Y{valid_y:02X}"

    tester.poke(circuit.interface[wen], 1)

    counter = 0
    for i in range(200):
        tester.poke(circuit.interface[src], counter)
        tester.eval()

        if i == depth - 1:
            tester.expect(circuit.interface[valid], 0)
            tester.poke(circuit.interface[wen], 0)
        elif i == depth:
            tester.poke(circuit.interface[wen], 1)
            tester.expect(circuit.interface[valid], 0)
            counter += 1
        elif i >= depth + 1:
            tester.expect(circuit.interface[dst], i * 2 - depth - 2)
            tester.expect(circuit.interface[valid], 1)
            counter += 1
        else:
            tester.expect(circuit.interface[valid], 0)
            counter += 1

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
        for aoi_mux in glob.glob("tests/*.sv"):
            shutil.copy(aoi_mux, tempdir)
        tester.compile_and_run(target="verilator",
                               magma_output="coreir-verilog",
                               directory=tempdir,
                               flags=["-Wno-fatal"])


@pytest.mark.parametrize("add_pd", [True, False])
def test_interconnect_sram(cw_files, add_pd, io_sides):
    chip_size = 2
    interconnect = create_cgra(chip_size, chip_size, io_sides,
                               num_tracks=3,
                               add_pd=add_pd,
                               mem_ratio=(1, 2))

    netlist = {
        "e0": [("I0", "io2f_16"), ("m0", "addr_in")],
        "e1": [("m0", "data_out"), ("I1", "f2io_16")],
        "e2": [("i3", "io2f_1"), ("m0", "ren_in")]
    }
    bus = {"e0": 16, "e1": 16, "e2": 1}

    placement, routing = pnr(interconnect, (netlist, bus))
    config_data = interconnect.get_route_bitstream(routing)

    x, y = placement["m0"]
    memtile = interconnect.tile_circuits[(x, y)]
    mode = Mode.SRAM
    mcore = memtile.core
    config_data.append((interconnect.get_config_addr(
                        mcore.get_reg_index("mode"),
                        0, x, y), mode.value))
    config_data.append((interconnect.get_config_addr(
                        mcore.get_reg_index("tile_en"),
                        0, x, y), 1))

    # in this case we configure (1, 0) as sram mode
    sram_data = []
    # add SRAM data
    for i in range(0, 1024, 4):
        feat_addr = i // 256 + 1
        mem_addr = i % 256
        sram_data.append((interconnect.get_config_addr(mem_addr, feat_addr, x,
                                                       y),
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
    src = f"glb2io_16_X{addr_x:02X}_Y{addr_y:02X}"
    dst_x, dst_y = placement["I1"]
    dst = f"io2glb_16_X{dst_x:02X}_Y{dst_y:02X}"
    ren_x, ren_y = placement["i3"]
    ren = f"glb2io_1_X{ren_x:02X}_Y{ren_y:02X}"

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
        for aoi_mux in glob.glob("tests/*.sv"):
            shutil.copy(aoi_mux, tempdir)
        tester.compile_and_run(target="verilator",
                               magma_output="coreir-verilog",
                               directory=tempdir,
                               flags=["-Wno-fatal"])
