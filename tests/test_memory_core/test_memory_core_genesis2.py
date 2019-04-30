from memory_core import memory_core_genesis2
from memory_core.memory_core import gen_memory_core, Mode
import glob
import os
import shutil
import fault
import random
from hwtypes import BitVector
from gemstone.common.testers import ResetTester, ConfigurationTester
from gemstone.common.collections import HashableDict


def teardown_function():
    for item in glob.glob('genesis_*'):
        os.system(f"rm -r {item}")
    os.system(f"rm MEMmemory_core")


def test_main(capsys):
    argv = [
        "--data_width", "16",
        "--data_depth", "1024",
        "memory_core/genesis/input_sr.vp",
        "memory_core/genesis/output_sr.vp",
        "memory_core/genesis/linebuffer_control.vp",
        "memory_core/genesis/fifo_control.vp",
        "memory_core/genesis/mem.vp",
        "memory_core/genesis/memory_core.vp"
    ]
    memory_core_genesis2.memory_core_wrapper.main(
        argv=argv,
        param_mapping=HashableDict(memory_core_genesis2.param_mapping))
    out, _ = capsys.readouterr()
    assert out == f"""\
Running genesis cmd 'Genesis2.pl -parse -generate -top memory_core -input memory_core/genesis/input_sr.vp memory_core/genesis/output_sr.vp memory_core/genesis/linebuffer_control.vp memory_core/genesis/fifo_control.vp memory_core/genesis/mem.vp memory_core/genesis/memory_core.vp -parameter memory_core.dwidth='16' -parameter memory_core.ddepth='1024''
memory_core(clk_in: In(Clock), clk_en: In(Bit), reset: In(AsyncReset), config_addr: In(Bits[32]), config_data: In(Bits[32]), config_read: In(Bit), config_write: In(Bit), config_en: In(Enable), config_en_sram: In(Bits[4]), config_en_linebuf: In(Bit), data_in: In(Bits[16]), data_out: Out(Bits[16]), wen_in: In(Bit), ren_in: In(Bit), valid_out: Out(Bit), chain_in: In(Bits[16]), chain_out: Out(Bits[16]), chain_wen_in: In(Bit), chain_valid_out: Out(Bit), almost_full: Out(Bit), almost_empty: Out(Bit), addr_in: In(Bits[16]), read_data: Out(Bits[32]), read_data_sram_0: Out(Bits[32]), read_data_sram_1: Out(Bits[32]), read_data_sram_2: Out(Bits[32]), read_data_sram_3: Out(Bits[32]), read_data_linebuf: Out(Bits[32]), flush: In(Bit))
"""  # nopep8


class MemoryCoreTester(ResetTester, ConfigurationTester):
    def write(self, addr, data):
        self.functional_model.write(addr, data)
        self.poke(self._circuit.clk_in, 0)
        self.poke(self._circuit.wen_in, 1)
        self.poke(self._circuit.addr_in, addr)
        self.poke(self._circuit.data_in, data)
        self.eval()
        self.poke(self._circuit.clk_in, 1)
        self.eval()
        self.poke(self._circuit.wen_in, 0)

    def read(self, addr):
        self.poke(self._circuit.clk_in, 0)
        self.poke(self._circuit.wen_in, 0)
        self.poke(self._circuit.addr_in, addr)
        self.poke(self._circuit.ren_in, 1)
        self.eval()

        self.poke(self._circuit.clk_in, 1)
        self.eval()
        self.poke(self._circuit.ren_in, 0)
        # 1-cycle read delay
        self.poke(self._circuit.clk_in, 0)
        self.eval()

        self.functional_model.read(addr)
        self.poke(self._circuit.clk_in, 1)
        self.eval()
        # Don't expect anything after for now
        self.functional_model.data_out = fault.AnyValue

    def read_and_write(self, addr, data):
        self.poke(self._circuit.clk_in, 0)
        self.poke(self._circuit.ren_in, 1)
        self.poke(self._circuit.wen_in, 1)
        self.poke(self._circuit.addr_in, addr)
        self.poke(self._circuit.data_in, data)
        self.eval()
        self.poke(self._circuit.clk_in, 1)
        self.eval()
        self.poke(self._circuit.wen_in, 0)
        self.poke(self._circuit.ren_in, 0)
        self.poke(self._circuit.clk_in, 0)
        self.eval()
        self.poke(self._circuit.clk_in, 1)
        self.functional_model.read_and_write(addr, data)
        self.eval()


def test_sram_basic():
    generator = memory_core_genesis2.memory_core_wrapper.generator(
        param_mapping=HashableDict(memory_core_genesis2.param_mapping))
    Mem = generator()  # Using default params
    for genesis_verilog in glob.glob("genesis_verif/*.v"):
        shutil.copy(genesis_verilog, "tests/test_memory_core/build")

    # FIXME: HACK from old CGRA, copy sram stub
    shutil.copy("tests/test_memory_core/sram_stub.v",
                "tests/test_memory_core/build/sram_512w_16b.v")

    # Setup functiona model
    DATA_DEPTH = 1024
    DATA_WIDTH = 16
    MemFunctionalModel = gen_memory_core(DATA_WIDTH, DATA_DEPTH)
    mem_functional_model_inst = MemFunctionalModel()

    tester = MemoryCoreTester(Mem, clock=Mem.clk_in,
                              functional_model=mem_functional_model_inst)
    tester.zero_inputs()
    tester.expect_any_outputs()

    tester.eval()

    tester.poke(Mem.clk_en, 1)

    tester.reset()

    mode = Mode.SRAM
    tile_enable = 1
    depth = 8
    config_data = mode.value | (tile_enable << 2) | (depth << 3)
    config_addr = BitVector(0, 32)
    tester.configure(config_addr, BitVector(config_data, 32))
    num_writes = 20
    memory_size = 1024

    def get_fresh_addr(reference):
        """
        Convenience function to get an address not already in reference
        """
        addr = random.randint(0, memory_size - 1)
        while addr in reference:
            addr = random.randint(0, memory_size - 1)
        return addr

    addrs = set()
    # Perform a sequence of random writes
    for i in range(num_writes):
        addr = get_fresh_addr(addrs)
        # TODO: Should be parameterized by data_width
        data = random.randint(0, (1 << 10))
        tester.write(addr, data)
        addrs.add(addr)

    # Read the values we wrote to make sure they are there
    for addr in addrs:
        tester.read(addr)

    for i in range(num_writes):
        addr = get_fresh_addr(addrs)
        tester.read_and_write(addr, random.randint(0, (1 << 10)))
        tester.read(addr)

    tester.compile_and_run(directory="tests/test_memory_core/build",
                           magma_output="verilog",
                           target="verilator",
                           flags=["-Wno-fatal"])
