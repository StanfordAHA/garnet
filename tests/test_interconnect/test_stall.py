import tempfile
import glob
import shutil
import os
from gemstone.common.testers import BasicTester
from canal.util import IOSide
import lassen.asm as asm
from archipelago import pnr
import pytest
from cgra import create_cgra
from memory_core.memory_mode import Mode


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


def test_stall(dw_files, io_sides):
    chip_size = 2
    depth = 10
    interconnect = create_cgra(chip_size, chip_size, io_sides,
                               num_tracks=3,
                               add_pd=True,
                               mem_ratio=(1, 2))

    netlist = {
        "e0": [("I0", "io2f_16"), ("r1", "reg")],
        "e2": [("r1", "reg"), ("m0", "data_in"), ("p0", "data0")],
        "e1": [("m0", "data_out"), ("p0", "data1")],
        "e3": [("p0", "alu_res"), ("I1", "f2io_16")],
        "e4": [("i3", "io2f_1"), ("m0", "wen_in")],
        "e5": [("m0", "valid_out"), ("i4", "f2io_1")]
    }
    bus = {"e0": 16, "e2": 16, "e1": 16, "e3": 16, "e4": 1, "e5": 1}

    placement, routing = pnr(interconnect, (netlist, bus))
    config_data = interconnect.get_route_bitstream(routing)

    x, y = placement["p0"]

    tile = interconnect.tile_circuits[(x, y)]
    add_bs = tile.core.get_config_bitstream(asm.add(ra_mode=asm.Mode_t.DELAY))
    for addr, data in add_bs:
        config_data.append((interconnect.get_config_addr(addr, 0, x, y), data))

    tile_en = 1

    mem_x, mem_y = placement["m0"]
    memtile = interconnect.tile_circuits[(mem_x, mem_y)]
    mcore = memtile.core
    config_data.append((interconnect.get_config_addr(
                        mcore.get_reg_index("depth"),
                        0, mem_x, mem_y), depth))
    config_data.append((interconnect.get_config_addr(
                        mcore.get_reg_index("mode"),
                        0, mem_x, mem_y), Mode.DB.value))
    config_data.append((interconnect.get_config_addr(
                        mcore.get_reg_index("tile_en"),
                        0, mem_x, mem_y), tile_en))
    config_data.append((interconnect.get_config_addr(
                        mcore.get_reg_index("rate_matched"),
                        0, mem_x, mem_y), 1))
    config_data.append((interconnect.get_config_addr(
                        mcore.get_reg_index("stencil_width"),
                        0, mem_x, mem_y), 0))
    config_data.append((interconnect.get_config_addr(
                        mcore.get_reg_index("iter_cnt"),
                        0, mem_x, mem_y), depth))
    config_data.append((interconnect.get_config_addr(
                        mcore.get_reg_index("dimensionality"),
                        0, mem_x, mem_y), 1))
    config_data.append((interconnect.get_config_addr(
                        mcore.get_reg_index("stride_0"),
                        0, mem_x, mem_y), 1))
    config_data.append((interconnect.get_config_addr(
                        mcore.get_reg_index("range_0"),
                        0, mem_x, mem_y), depth))
    config_data.append((interconnect.get_config_addr(
                        mcore.get_reg_index("flush_reg_sel"),
                        0, mem_x, mem_y), 1))
    config_data.append((interconnect.get_config_addr(
                        mcore.get_reg_index("switch_db_reg_sel"),
                        0, mem_x, mem_y), 1))

    circuit = interconnect.circuit()

    tester = BasicTester(circuit, circuit.clk, circuit.reset)
    tester.reset()

    # stall the chip
    tester.poke(circuit.interface["stall"], 1)
    tester.eval()

    for addr, index in config_data:
        tester.configure(addr, index)
        tester.config_read(addr)
        tester.eval()
        tester.expect(circuit.read_config_data, index)

    # un-stall the chp
    # stall the chip
    tester.poke(circuit.interface["stall"], 0)
    tester.eval()

    src_x, src_y = placement["I0"]
    src = f"glb2io_16_X{src_x:02X}_Y{src_y:02X}"
    dst_x, dst_y = placement["I1"]
    dst = f"io2glb_16_X{dst_x:02X}_Y{dst_y:02X}"
    wen_x, wen_y = placement["i3"]
    wen = f"glb2io_1_X{wen_x:02X}_Y{wen_y:02X}"
    valid_x, valid_y = placement["i4"]
    valid = f"io2glb_1_X{valid_x:02X}_Y{valid_y:02X}"

    tester.poke(circuit.interface[wen], 1)

    for i in range(20):
        tester.poke(circuit.interface[src], i)
        tester.eval()
        if i >= 10 + 1:
            # data0 of PE: i - 1 - 1
            # data1 of PE: i - 1 - depth
            tester.expect(circuit.interface[dst], i * 2 - 3 - depth)
            tester.expect(circuit.interface[valid], 1)
        elif i < depth:
            tester.expect(circuit.interface[valid], 0)
        if i == 19:
            # now stall everything
            tester.poke(circuit.interface["stall"], 1)
            tester.eval()
        tester.step(2)

    for i in range(20):
        # poke random numbers. it shouldn't matter
        tester.poke(circuit.interface[src], i * 20)
        tester.expect(circuit.interface[dst], 19 * 2 - 3 - depth)
        tester.step(2)

    # un-stall again
    tester.poke(circuit.interface["stall"], 0)
    tester.eval()

    for i in range(19, 30):
        tester.poke(circuit.interface[src], i)
        tester.eval()
        tester.expect(circuit.interface[dst], i * 2 - 3 - depth)
        tester.expect(circuit.interface[valid], 1)
        tester.step(2)

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
