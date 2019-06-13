from gemstone.common.testers import BasicTester
from peak_core.peak_core import PeakCore
from lassen.sim import gen_pe
from lassen.asm import add, Mode
import shutil
import tempfile
import os
import pytest


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


def test_pe_config(cw_files):
    core = PeakCore(gen_pe)
    core.name = lambda: "PECore"
    circuit = core.circuit()

    # random test stuff
    tester = BasicTester(circuit, circuit.clk, circuit.reset)
    tester.reset()

    tester.poke(circuit.interface["stall"], 1)
    config_data = core.get_config_bitstream(add(Mode.DELAY, Mode.DELAY))
    # hacky way to configure it as 0x42 + 0x42 from the operand register
    config_data += [(3, 0x42 << 16 | 0x42)]
    for addr, data in config_data:
        print("{0:08X} {1:08X}".format(addr, data))
        tester.configure(addr, data)
        tester.config_read(addr)
        tester.eval()
        tester.expect(circuit.read_config_data, data)

    for i in range(10):
        tester.poke(circuit.interface["data0"], i + 1)
        tester.poke(circuit.interface["data1"], i + 1)
        tester.eval()
        tester.expect(circuit.interface["alu_res"], 0x42 + 0x42)

    with tempfile.TemporaryDirectory() as tempdir:
        for filename in cw_files:
            shutil.copy(filename, tempdir)
        tester.compile_and_run(target="verilator",
                               magma_output="coreir-verilog",
                               magma_opts={"coreir_libs": {"float_CW"}},
                               directory=tempdir,
                               flags=["-Wno-fatal"])
