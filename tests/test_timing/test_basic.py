import glob
import os
import pytest
import shutil
import tempfile
from canal.cyclone import SwitchBoxSide, SwitchBoxIO
from canal.util import IOSide
from gemstone.common.testers import BasicTester
import hwtypes
import lassen.asm
import magma
from cgra import create_cgra


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


def test_interconnect_point_wise(dw_files):
    """
    Pointwise multiply test on 2x2 fabric, without IO tiles. Routing and
    placement is hand-crafted.
    """
    # Create cgra generator object. Note that we set standalone=True,
    # io_sides=IOSide.None_, and mem_ratio=(1, 100). These options specify that
    # interconnect ports are lifted to the top, IO tiles are not included, and
    # that there are no Mem tiles (for a 2x2).
    chip_size = 2
    interconnect = create_cgra(width=chip_size, height=chip_size, num_tracks=5,
                               add_pd=True)

    config_data = []

    # Configure Tile(0, 0).PE to be umult0.
    pe_tile = interconnect.tile_circuits[(0, 0)]
    mul_conifg_data = pe_tile.core.get_config_bitstream(lassen.asm.umult0())
    for addr, data in mul_conifg_data:
        full_addr = interconnect.get_config_addr(addr, 0, 0, 0)
        config_data.append((full_addr, data))

    # Construct circuit and setup fault tester.
    circuit = interconnect.circuit()

    tester = BasicTester(circuit, circuit.clk, circuit.reset)
    tester.circuit.clk = 0
    tester.print(f"Starting reset\n")
    tester.reset()
    tester.print(f"Finished reset\n")

    MAX_CONFIG = 2
    # Run configuration sequence and check the configuration output bus. Only do
    # a maximum of 2 config's.
    for i, (addr, data) in enumerate(config_data):
        if i > MAX_CONFIG:
            break
        tester.configure(addr, data)
        tester.config_read(addr)
        tester.eval()
        tester.print(f"Doing config {(addr, data)}\n")
        tester.expect(circuit.read_config_data, data)
    tester.done_config()

    # Compile and run the test using a verilator backend.
    ext_srcs = [f"{circuit.name}.sv", "DW_fp_add.v", "DW_fp_mult.v",
                "AN2D0BWP16P90.sv", "AO22D0BWP16P90.sv"]
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
        magma.compile(f"{tempdir}/{circuit.name}", circuit,
                      output="coreir-verilog", coreir_libs={"float_DW"},
                      sv=True)
        tester.compile_and_run(skip_compile=True, target="system-verilog",
                               simulator="ncsim", directory=tempdir,
                               ext_model_file=True, ext_srcs=ext_srcs,
                               skip_run=True)
