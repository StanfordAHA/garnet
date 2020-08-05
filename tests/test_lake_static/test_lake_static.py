from memory_core.memory_core import gen_memory_core, Mode
from memory_core.memory_core_magma import MemCore
from memory_core.memory_core_magma import transform_strides_and_ranges
import glob
import tempfile
import shutil
import fault
import random
import magma
from gemstone.common.testers import ResetTester
from gemstone.common.testers import BasicTester
import pytest
from gemstone.generator import Const


def make_memory_core():
    mem_core = MemCore()
    mem_circ = mem_core.circuit()

    tester = MemoryCoreTester(mem_circ, mem_circ.clk, mem_circ.reset)
    tester.poke(mem_circ.clk, 0)
    tester.poke(mem_circ.reset, 0)
    tester.step(1)
    tester.poke(mem_circ.reset, 1)
    tester.step(1)
    tester.reset()
    return [mem_circ, tester, mem_core]


class MemoryCoreTester(BasicTester):

    def configure(self, addr, data, feature):
        self.poke(self.clock, 0)
        self.poke(self.reset_port, 0)
        if(feature == 0):
            exec(f"self.poke(self._circuit.config.config_addr, addr)")
            exec(f"self.poke(self._circuit.config.config_data, data)")
            exec(f"self.poke(self._circuit.config.write, 1)")
            self.step(1)
            exec(f"self.poke(self._circuit.config.write, 0)")
            exec(f"self.poke(self._circuit.config.config_data, 0)")
        else:
            exec(f"self.poke(self._circuit.config_{feature}.config_addr, addr)")
            exec(f"self.poke(self._circuit.config_{feature}.config_data, data)")
            exec(f"self.poke(self._circuit.config_{feature}.write, 1)")
            self.step(1)
            exec(f"self.poke(self._circuit.config_{feature}.write, 0)")
            exec(f"self.poke(self._circuit.config_{feature}.config_data, 0)")


def basic_tb(config_path):

    # Regular Bootstrap
    [circuit, tester, MCore] = make_memory_core()
    tester.poke(circuit.stall, 1)

    config_simple = MCore.get_static_bitstream(config_path)

    config_data = []
    for cfg_reg, val in config_simple:
        config_data.append((MCore.get_reg_index(cfg_reg), val, 0))

    # Configure
    for addr, data, feat in config_data:
        tester.configure(addr, data, feat)

    tester.poke(circuit.stall, 0)
    tester.eval()

    output_idx = 0

    for i in range(64):

        tester.poke(circuit.wen_in, 1)
        tester.poke(circuit.data_in, output_idx)
        output_idx += 1

        tester.eval()

        tester.step(2)

    with tempfile.TemporaryDirectory() as tempdir:
        tempdir = "dump_2"
        # for genesis_verilog in glob.glob("genesis_verif/*.*"):
            # shutil.copy(genesis_verilog, tempdir)
        tester.compile_and_run(directory=tempdir,
                               magma_output="coreir-verilog",
                               target="system-verilog",
                               simulator="vcs",
                               flags=["-Wno-fatal", "--trace"])


if __name__ == "__main__":
    basic_tb("/Users/max/Documents/POND/clockwork/lake_controllers/dual_port_test")
