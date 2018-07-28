from memory_core import memory_core_genesis2
from memory_core.memory_core import gen_memory_core, Mode
import glob
import os
import shutil
import fault
import random
from bit_vector import BitVector
from common.testers import ResetTester, ConfigurationTester


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
        argv=argv, param_mapping=memory_core_genesis2.param_mapping)
    out, _ = capsys.readouterr()
    assert out == f"""\
Running genesis cmd 'Genesis2.pl -parse -generate -top memory_core -input memory_core/genesis/input_sr.vp memory_core/genesis/output_sr.vp memory_core/genesis/linebuffer_control.vp memory_core/genesis/fifo_control.vp memory_core/genesis/mem.vp memory_core/genesis/memory_core.vp -parameter memory_core.dwidth='16' -parameter memory_core.ddepth='1024''
memory_core(clk_in: In(Bit), clk_en: In(Bit), reset: In(Bit), config_addr: Array(32,In(Bit)), config_data: Array(32,In(Bit)), config_read: In(Bit), config_write: In(Bit), config_en: In(Bit), config_en_sram: Array(4,In(Bit)), config_en_linebuf: In(Bit), data_in: Array(16,In(Bit)), data_out: Array(16,Out(Bit)), wen_in: In(Bit), ren_in: In(Bit), valid_out: Out(Bit), chain_in: Array(16,In(Bit)), chain_out: Array(16,Out(Bit)), chain_wen_in: In(Bit), chain_valid_out: Out(Bit), almost_full: Out(Bit), almost_empty: Out(Bit), addr_in: Array(16,In(Bit)), read_data: Array(32,Out(Bit)), read_data_sram: Array(32,Out(Bit)), read_data_linebuf: Array(32,Out(Bit)), flush: In(Bit))
"""  # nopep8


class MemoryCoreTester(ResetTester, ConfigurationTester):
    def write(self, addr, data):
        self.functional_model.write(addr, data)
        self.poke(self.circuit.clk_in, 0)
        self.poke(self.circuit.wen_in, 1)
        self.poke(self.circuit.addr_in, addr)
        self.poke(self.circuit.data_in, data)
        self.eval()
        self.poke(self.circuit.clk_in, 1)
        self.eval()
        self.poke(self.circuit.wen_in, 0)

    def read(self, addr):
        self.poke(self.circuit.clk_in, 0)
        self.poke(self.circuit.wen_in, 0)
        self.poke(self.circuit.addr_in, addr)
        self.poke(self.circuit.ren_in, 1)
        self.eval()

        self.poke(self.circuit.clk_in, 1)
        self.eval()
        self.poke(self.circuit.ren_in, 0)
        # 1-cycle read delay
        self.poke(self.circuit.clk_in, 0)
        self.eval()

        self.functional_model.read(addr)
        self.poke(self.circuit.clk_in, 1)
        self.eval()
        # Don't expect anything after for now
        self.functional_model.data_out = None

    def read_and_write(self, addr, data):
        self.poke(self.circuit.clk_in, 0)
        self.poke(self.circuit.ren_in, 1)
        self.poke(self.circuit.wen_in, 1)
        self.poke(self.circuit.addr_in, addr)
        self.poke(self.circuit.data_in, data)
        self.eval()
        self.poke(self.circuit.clk_in, 1)
        self.eval()
        self.poke(self.circuit.wen_in, 0)
        self.poke(self.circuit.ren_in, 0)
        self.poke(self.circuit.clk_in, 0)
        self.eval()
        self.poke(self.circuit.clk_in, 1)
        self.functional_model.read_and_write(addr, data)
        self.eval()


def test_sram_basic():
    generator = memory_core_genesis2.memory_core_wrapper.generator(
        param_mapping=memory_core_genesis2.param_mapping)
    Mem = generator()  # Using default params
    for genesis_verilog in glob.glob("genesis_verif/*.v"):
        shutil.copy(genesis_verilog, "test_memory_core/build")

    # FIXME: HACK from old CGRA, copy sram stub
    shutil.copy("test_memory_core/sram_stub.v",
                "test_memory_core/build/sram_512w_16b.v")

    # Setup functiona model
    DATA_DEPTH = 1024
    DATA_WIDTH = 16
    MemFunctionalModel = gen_memory_core(DATA_WIDTH, DATA_DEPTH)
    mem_functional_model_inst = MemFunctionalModel()

    tester = MemoryCoreTester(Mem, clock=Mem.clk_in,
                              functional_model=mem_functional_model_inst)
    # Initialize all inputs to 0
    # TODO: Make this a convenience function in Tester?
    # We have to get the `outputs` because the ports are flipped to use the
    # polarity for definitions. TODO: This is a confusing wart
    for port in Mem.interface.outputs():
        tester.poke(getattr(Mem, str(port)), 0)

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

    tester.compile_and_run(directory="test_memory_core/build",
                           target="verilator", flags=["-Wno-fatal"])
