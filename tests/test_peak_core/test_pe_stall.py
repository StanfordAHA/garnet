from gemstone.common.testers import BasicTester
from peak_core.peak_core import PeakCore
from lassen.sim import PE_fc
from lassen.asm import add, Mode_t
import shutil
import tempfile
import os
import pytest


def test_pe_stall(run_tb):
    core = PeakCore(PE_fc)
    core.finalize()
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
        tester.expect(circuit.interface["res"], 0)

    run_tb(tester)
