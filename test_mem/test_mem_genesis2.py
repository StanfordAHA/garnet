from mem import mem_genesis2
import glob
import os
import shutil
import fault
from magma.testing.verilator import compile, run_verilator_test
from enum import Enum
import random


def teardown_function():
    for item in glob.glob('genesis_*'):
        os.system(f"rm -r {item}")
    os.system(f"rm MEMmemory_core")


def test_main(capsys):
    parser = mem_genesis2.create_parser()
    args = parser.parse_args([
        "--data-width", "16",
        "--data-depth", "1024",
        "mem/genesis/input_sr.vp",
        "mem/genesis/output_sr.vp",
        "mem/genesis/linebuffer_control.vp",
        "mem/genesis/fifo_control.vp",
        "mem/genesis/mem.vp",
        "mem/genesis/memory_core.vp"
    ])

    mem_genesis2.main(args)
    out, _ = capsys.readouterr()
    assert out == f"""\
Running genesis cmd 'Genesis2.pl -parse -generate -top memory_core -input mem/genesis/input_sr.vp mem/genesis/output_sr.vp mem/genesis/linebuffer_control.vp mem/genesis/fifo_control.vp mem/genesis/mem.vp mem/genesis/memory_core.vp -parameter memory_core.dwidth='16' -parameter memory_core.ddepth='1024''
memory_core(clk_in: In(Bit), clk_en: In(Bit), reset: In(Bit), config_addr: Array(32,In(Bit)), config_data: Array(32,In(Bit)), config_read: In(Bit), config_write: In(Bit), config_en: In(Bit), config_en_sram: Array(4,In(Bit)), config_en_linebuf: In(Bit), data_in: Array(16,In(Bit)), data_out: Array(16,Out(Bit)), wen_in: In(Bit), ren_in: In(Bit), valid_out: Out(Bit), chain_in: Array(16,In(Bit)), chain_out: Array(16,Out(Bit)), chain_wen_in: In(Bit), chain_valid_out: Out(Bit), almost_full: Out(Bit), almost_empty: Out(Bit), addr_in: Array(16,In(Bit)), read_data: Array(32,Out(Bit)), read_data_sram: Array(32,Out(Bit)), read_data_linebuf: Array(32,Out(Bit)), flush: In(Bit))
"""  # nopep8


def reset(tester, mem):
    """
    Reset sequence
    """
    tester.poke(mem.reset, 1)
    tester.poke(mem.clk_in, 1)
    # TODO: For some reason almost_empty is 1 after first eval, is this
    # expected? Also, we could just make this None (for X or don't care)
    tester.expect(mem.almost_empty, 1)
    tester.eval()
    tester.poke(mem.reset, 0)
    tester.poke(mem.clk_in, 0)
    tester.step()
    tester.step()


class Mode(Enum):
    LINE_BUFFER = 0
    FIFO = 1
    SRAM = 2


class MemTester(fault.Tester):
    def configure(self):
        """
        Configuration sequence
        """
        self.poke(self.circuit.clk_in, 0)
        self.eval()
        self.poke(self.circuit.config_en, 1)

        mode = Mode.SRAM
        tile_enable = 1
        depth = 8
        # TODO: Abstract this to functional model (configurable interface)
        config_data = mode.value | (tile_enable << 2) | (depth << 3)
        self.poke(self.circuit.config_data, config_data)
        self.poke(self.circuit.clk_in, 1)
        # Verify configuration, the value should be read_data
        self.expect(self.circuit.read_data, config_data)
        # Expect these default values for now (so we know if they change),
        # could be None/X though
        self.expect(self.circuit.valid_out, 1)
        self.expect(self.circuit.chain_valid_out, 1)
        self.expect(self.circuit.almost_empty, 0)
        self.eval()
        self.poke(self.circuit.config_en, 0)

    def write(self, addr, data):
        self.poke(self.circuit.clk_in, 0)
        self.eval()
        self.poke(self.circuit.wen_in, 1)
        self.poke(self.circuit.addr_in, addr)
        self.poke(self.circuit.data_in, data)
        self.poke(self.circuit.clk_in, 1)
        self.eval()
        self.poke(self.circuit.clk_in, 0)
        self.eval()
        self.poke(self.circuit.clk_in, 1)
        self.eval()
        self.poke(self.circuit.wen_in, 0)

    def expect_read(self, addr, data):
        self.poke(self.circuit.clk_in, 0)
        self.eval()
        # These values might change early, but we don't expect anything until
        # after the 1 cycle read delay
        self.expect(self.circuit.data_out, None)
        self.expect(self.circuit.chain_out, None)
        self.poke(self.circuit.wen_in, 0)
        self.poke(self.circuit.addr_in, addr)
        self.poke(self.circuit.ren_in, 1)
        self.poke(self.circuit.clk_in, 1)
        self.eval()

        # 1-cycle read delay
        self.poke(self.circuit.clk_in, 0)
        # TODO: sram_data might change early, but we expect a 1 cycle read
        # delay so we don't care about this. Should figure out the exact,
        # expected semantics for read_data_sram
        self.expect(self.circuit.read_data_sram, None)
        self.eval()

        self.poke(self.circuit.clk_in, 1)
        # Expect these values on the next eval (clock is on posedge)
        self.expect(self.circuit.data_out, data)
        self.expect(self.circuit.chain_out, data)
        self.eval()


def test_sram_basic():
    Mem = mem_genesis2.define_mem_genesis2()  # Using default params
    for genesis_verilog in glob.glob("genesis_verif/*.v"):
        shutil.copy(genesis_verilog, "test_mem/build")

    # FIXME: HACK from old CGRA, copy sram stub
    shutil.copy("test_mem/sram_stub.v", "test_mem/build/sram_512w_16b.v")

    tester = MemTester(Mem, clock=Mem.clk_in)
    # Initialize all inputs to 0
    # TODO: Make this a convenience function in Tester?
    # We have to get the `outputs` because the ports are flipped to use the
    # polarity for definitions. TODO: This is a confusing wart
    for port in Mem.interface.outputs():
        tester.poke(getattr(Mem, str(port)), 0)

    # Expect all outputs to be 0
    for port in Mem.interface.inputs():
        tester.expect(getattr(Mem, str(port)), 0)

    tester.eval()
    tester.poke(Mem.clk_en, 1)

    reset(tester, Mem)

    tester.configure()
    num_writes = 5
    memory_size = 1024
    reference = {}

    def get_fresh_addr(reference):
        """
        Convenience function to get an address not already in reference
        """
        addr = random.randint(0, memory_size)
        while addr in reference:
            addr = random.randint(0, memory_size)
        return addr

    # Perform a sequence of random writes
    for i in range(num_writes):
        addr = get_fresh_addr(reference)
        # TODO: Should be parameterized by data_width
        data = random.randint(0, (1 << 10))
        reference[addr] = data
        tester.write(addr, data)

    # Read the values we wrote to make sure they are there
    for addr, data in reference.items():
        tester.expect_read(addr, data)

    compile(f"test_mem/build/test_{Mem.name}.cpp", Mem, tester.test_vectors)
    run_verilator_test(Mem.name, f"test_{Mem.name}", Mem.name, ["-Wno-fatal"],
                       build_dir="test_mem/build")
