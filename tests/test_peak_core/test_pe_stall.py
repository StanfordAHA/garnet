from gemstone.common.testers import BasicTester
from peak_core.peak_core import PeakCore
from lassen.sim import PE_fc
from lassen.asm import add, Mode_t
import shutil
import tempfile
import os
import pytest


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


def test_pe_stall(dw_files):
    core = PeakCore(PE_fc)
    core.name = lambda: "PECore"
    circuit = core.circuit()

    # random test stuff
    tester = BasicTester(circuit, circuit.clk, circuit.reset)
    tester.reset()

    tester.poke(circuit.interface["stall"], 1)
    config_data = core.get_config_bitstream(add(ra_mode=Mode_t.DELAY,
                                                rb_mode=Mode_t.DELAY))

    for addr, data in config_data:
        tester.configure(addr, data)
        # can't read back yet

    for i in range(100):
        tester.poke(circuit.interface["data0"], i + 1)
        tester.poke(circuit.interface["data1"], i + 1)
        tester.eval()
        tester.expect(circuit.interface["alu_res"], 0)

    with tempfile.TemporaryDirectory() as tempdir:
        for filename in dw_files:
            shutil.copy(filename, tempdir)
        tester.compile_and_run(target="verilator",
                               magma_output="coreir-verilog",
                               magma_opts={"coreir_libs": {"float_DW"},
                                           "inline": False},
                               directory=tempdir,
                               flags=["-Wno-fatal"])
