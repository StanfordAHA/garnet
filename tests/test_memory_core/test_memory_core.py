from memory_core import memory_core_genesis2
from memory_core.memory_core import gen_memory_core, Mode
import glob
import os
import tempfile
import shutil
import fault
import random
from hwtypes import BitVector
from gemstone.common.testers import ResetTester, ConfigurationTester
from memory_core.memory_core_magma import MemCore
import magma
import canal
import coreir
from gemstone.generator.generator import Generator
from gemstone.common.testers import BasicTester


def make_memory_core():
    mem_core = MemCore(16, 16, 512, 2)
    mem_circ = mem_core.circuit()
    # Setup functional model
    DATA_DEPTH = 1024
    DATA_WIDTH = 16
    MemFunctionalModel = gen_memory_core(DATA_WIDTH, DATA_DEPTH)
    mem_functional_model_inst = MemFunctionalModel()
    tester = MemoryCoreTester(mem_circ, clock=mem_circ.clk_in,
                              functional_model=mem_functional_model_inst)
    tester.hand_highlevel(mem_core)
    tester.reset()
    return [mem_circ, tester]


class MemoryCoreTester(ResetTester, BasicTester):

    def hand_highlevel(self, hl):
        self.__hl_circ = hl

    def configure(self, addr, data, feature):
        self.poke(self.clock, 0)
        self.poke(self.reset_port, 0)
        exec(f"self.poke(self._circuit.config_{feature}.config_addr, addr)")
        exec(f"self.poke(self._circuit.config_{feature}.config_data, data)")
        exec(f"self.poke(self._circuit.config_{feature}.write, 1)")
        self.step(2)
        exec(f"self.poke(self._circuit.config_{feature}.write, 0)")
        exec(f"self.poke(self._circuit.config_{feature}.config_data, 0)")

    def write(self, data, addr=0):
        self.functional_model.write(addr, data)
        # \_
        self.poke(self._circuit.clk_in, 0)
        self.poke(self._circuit.wen_in, 1)
        self.poke(self._circuit.addr_in, addr)
        self.poke(self._circuit.data_in, data)
        self.eval()

        # _/
        self.poke(self._circuit.clk_in, 1)
        self.eval()
        self.poke(self._circuit.wen_in, 0)

    def write_and_observe(self, data, addr=0):
        self.functional_model.read(addr)
        self.functional_model.write(addr, data)
        self.eval()
        # \_
        self.poke(self._circuit.clk_in, 0)
        self.poke(self._circuit.wen_in, 1)
        self.poke(self._circuit.addr_in, addr)
        self.poke(self._circuit.data_in, data)
        self.eval()

        # _/
        self.poke(self._circuit.clk_in, 1)

    def observe(self, addr=0):
        self.functional_model.read(addr)
        self.eval()
        # \_
        self.poke(self._circuit.clk_in, 0)
        self.poke(self._circuit.wen_in, 1)
        self.poke(self._circuit.addr_in, addr)
        self.eval()

        # _/
        self.poke(self._circuit.clk_in, 1)

    def read(self, addr=0):
        # \_
        self.poke(self._circuit.clk_in, 0)
        self.poke(self._circuit.wen_in, 0)
        self.poke(self._circuit.addr_in, addr)
        self.poke(self._circuit.ren_in, 1)
        self.eval()

        # _/
        self.poke(self._circuit.clk_in, 1)
        self.eval()
        self.poke(self._circuit.ren_in, 0)

        self.poke(self._circuit.clk_in, 0)
        self.eval()

        self.poke(self._circuit.clk_in, 1)

        self.functional_model.read(addr)
        self.eval()
        # Don't expect anything after for now
        self.functional_model.data_out = fault.AnyValue

    def read_and_write(self, data, addr=0):
        # \_
        self.poke(self._circuit.clk_in, 0)
        self.poke(self._circuit.ren_in, 1)
        self.poke(self._circuit.wen_in, 1)
        self.poke(self._circuit.addr_in, addr)
        self.poke(self._circuit.data_in, data)
        self.eval()

        # _/
        self.poke(self._circuit.clk_in, 1)
        self.functional_model.read_and_write(addr, data)
        self.eval()
        self.poke(self._circuit.wen_in, 0)
        self.poke(self._circuit.ren_in, 0)
        self.eval()


def test_passthru_fifo(depth=50, read_cadence=2):
    # Regular Bootstrap
    [Mem, tester] = make_memory_core()
    mode = Mode.FIFO
    tile_enable = 1
    config_data = []
    config_data.append((0, mode.value | (tile_enable << 2) | (depth << 3), 0))
    tester.functional_model.config_fifo(depth)
    for addr, data, feat in config_data:
        tester.configure(addr, data, feat)
    # Configure
    for i in range(27):
        tester.write(i + 1)

    tester.read_and_write(42)
    tester.read_and_write(43)
    tester.read_and_write(44)

    with tempfile.TemporaryDirectory() as tempdir:
        for genesis_verilog in glob.glob("genesis_verif/*.*"):
            shutil.copy(genesis_verilog, tempdir)
        tester.compile_and_run(directory=tempdir,
                               magma_output="coreir-verilog",
                               target="verilator",
                               flags=["-Wno-fatal"])


def test_fifo_arb(depth=50):
    [Mem, tester] = make_memory_core()
    mode = Mode.FIFO
    tile_enable = 1
    config_data = []
    config_data.append((0, mode.value | (tile_enable << 2) | (depth << 3), 0))
    # Configure the functional model in much the same way as the actual device
    tester.functional_model.config_fifo(depth)
    for addr, data, feat in config_data:
        tester.configure(addr, data, feat)
    for i in range(10):
        for i in range(depth):
            tester.write(random.randint(1, 101))
        for i in range(depth):
            tester.read()


def test_general_fifo():
    fifo(50, 6)


def fifo(depth=50, read_cadence=2):
    [Mem, tester] = make_memory_core()
    mode = Mode.FIFO
    tile_enable = 1
    config_data = []
    config_data.append((0, mode.value | (tile_enable << 2) | (depth << 3), 0))
    # Configure the functional model in much the same way as the actual device
    tester.functional_model.config_fifo(depth)
    for addr, data, feat in config_data:
        tester.configure(addr, data, feat)
    # do depth writes, then read
    for i in range(depth):
        if(i % read_cadence == 0):
            tester.read_and_write(i + 1)
        else:
            tester.write(i + 1)

    with tempfile.TemporaryDirectory() as tempdir:
        for genesis_verilog in glob.glob("genesis_verif/*.*"):
            shutil.copy(genesis_verilog, tempdir)
        tester.compile_and_run(directory=tempdir,
                               magma_output="coreir-verilog",
                               target="verilator",
                               flags=["-Wno-fatal"])


def test_db_basic_read():
    # Basic access
    db_basic(0, 1, 2, 3, 4, 5,
             1, 3, 9, 0, 0, 0,
             3, 3, 3, 1, 1, 1,
             3)


def test_db_long_read():
    # More advanced access
    db_basic(0, 1, 2, 3, 4, 5,
             1, 3, 1, 3, 9, 0,
             2, 2, 2, 2, 3, 1,
             5)


def test_db_read_mode():
    # Test read mode
    db_basic(0, 1, 2, 3, 4, 5,
             1, 3, 9, 0, 0, 0,
             3, 3, 3, 1, 1, 1,
             3,
             0,
             1)


def test_db_arbitrary_rw_addr():

    [Mem, tester] = make_memory_core()
    memory_size = 1024
    ranges = [1, 1, 1, 1, 1, 1]
    strides = [1, 1, 1, 1, 1, 1]
    tester.functional_model.config_db(memory_size, ranges, strides,
                                      0, 1, 3, 1)

    read_mode = 1
    arbitrary_addr = 1
    mode = Mode.DB
    tile_enable = 1
    depth = 130
    config_data = []
    config_data.append((0, (depth << 3) | (tile_enable << 2) | mode.value, 0))
    config_data.append((0, read_mode, 7))
    config_data.append((1, arbitrary_addr, 7))

    for addr, data, feat in config_data:
        tester.configure(addr, data, feat)

    for i in range(100):
        tester.write((i + 1))

    tester.poke(Mem.clk_in, 0)
    tester.poke(Mem.switch_db, 1)
    tester.eval()
    tester.poke(Mem.clk_in, 1)
    tester.eval()
    tester.poke(Mem.clk_in, 0)
    tester.poke(Mem.switch_db, 0)
    tester.functional_model.switch()

    for i in range(100):
        randaddr = random.randint(0, 99)
        tester.read_and_write(i + 1, randaddr)

    tester.poke(Mem.clk_in, 0)
    tester.poke(Mem.switch_db, 1)
    tester.functional_model.data_out = fault.AnyValue
    tester.eval()
    tester.poke(Mem.clk_in, 1)
    tester.eval()
    tester.poke(Mem.clk_in, 0)
    tester.poke(Mem.switch_db, 0)
    tester.functional_model.switch()
    # tester.functional_model.clear_db()
    tester.functional_model.data_out = fault.AnyValue

    for i in range(100):
        randaddr = random.randint(0, 99)
        tester.read(randaddr)

    with tempfile.TemporaryDirectory() as tempdir:
        for genesis_verilog in glob.glob("genesis_verif/*.*"):
            shutil.copy(genesis_verilog, tempdir)
        tester.compile_and_run(directory=tempdir,
                               magma_output="coreir-verilog",
                               target="verilator",
                               flags=["-Wno-fatal"])


def test_db_arbitrary_addr():

    [Mem, tester] = make_memory_core()
    memory_size = 1024
    ranges = [1, 1, 1, 1, 1, 1]
    strides = [1, 1, 1, 1, 1, 1]
    tester.functional_model.config_db(memory_size, ranges, strides,
                                      0, 1, 3, 1)

    read_mode = 1
    arbitrary_addr = 1
    mode = Mode.DB
    tile_enable = 1
    depth = 130
    config_data = []
    config_data.append((0, (depth << 3) | (tile_enable << 2) | mode.value, 0))
    config_data.append((0, read_mode, 7))
    config_data.append((1, arbitrary_addr, 7))

    for addr, data, feat in config_data:
        tester.configure(addr, data, feat)

    for i in range(100):
        tester.write((i + 1))

    tester.poke(Mem.clk_in, 0)
    tester.poke(Mem.switch_db, 1)
    tester.eval()
    tester.poke(Mem.clk_in, 1)
    tester.eval()
    tester.poke(Mem.clk_in, 0)
    tester.poke(Mem.switch_db, 0)
    tester.functional_model.switch()
    tester.functional_model.data_out = fault.AnyValue

    for i in range(100):
        randaddr = random.randint(0, 99)
        tester.read(randaddr)

    for i in range(100):
        tester.write((i + 1))

    tester.poke(Mem.clk_in, 0)
    tester.poke(Mem.switch_db, 1)
    tester.eval()
    tester.poke(Mem.clk_in, 1)
    tester.eval()
    tester.poke(Mem.clk_in, 0)
    tester.poke(Mem.switch_db, 0)
    tester.functional_model.switch()

    for i in range(100):
        randaddr = random.randint(0, 99)
        tester.read(randaddr)

    with tempfile.TemporaryDirectory() as tempdir:
        for genesis_verilog in glob.glob("genesis_verif/*.*"):
            shutil.copy(genesis_verilog, tempdir)
        tester.compile_and_run(directory=tempdir,
                               magma_output="coreir-verilog",
                               target="verilator",
                               flags=["-Wno-fatal", "--trace"])


def test_db_auto():
    db_auto(0, 1, 2, 3, 4, 5,
            1, 3, 9, 0, 0, 0,
            3, 3, 3, 1, 1, 1,
            3, 27)


def test_db_auto2():
    db_auto(0, 1, 2, 3, 4, 5,
            1, 3, 1, 3, 9, 0,
            2, 2, 2, 2, 3, 1,
            5, 27)


def db_auto(order0, order1, order2, order3, order4, order5,
            stride0, stride1, stride2, stride3, stride4, stride5,
            size0, size1, size2, size3, size4, size5,
            dimensionality, input_size,
            start_address=0,
            read_mode=0, manual_switch=0, arbitrary_addr=0):

    [Mem, tester] = make_memory_core()
    max_count = size0 * size1 * size2 * size3 * size4 * size5
    depth = input_size
    ranges = [size0, size1, size2, size3, size4, size5]
    strides = [stride0, stride1, stride2, stride3, stride4, stride5]
    tester.functional_model.config_db(depth, ranges, strides,
                                      start_address,
                                      manual_switch, dimensionality)
    # Assumes all ranges are 1 minimally

    mode = Mode.DB
    tile_enable = 1
    config_data = []
    config_data.append((0, (depth << 3) | (tile_enable << 2) | mode.value, 0))
    config_data.append((0, read_mode, 7))
    config_data.append((1, arbitrary_addr, 7))
    config_data.append((2, start_address, 7))
    config_data.append((3, dimensionality, 7))
    config_data.append((4, stride0, 7))
    config_data.append((5, order0, 7))
    config_data.append((6, size0, 7))
    config_data.append((7, stride1, 7))
    config_data.append((8, order1, 7))
    config_data.append((9, size1, 7))
    config_data.append((10, stride2, 7))
    config_data.append((11, order2, 7))
    config_data.append((12, size2, 7))
    config_data.append((13, stride3, 7))
    config_data.append((14, order3, 7))
    config_data.append((15, size3, 7))
    config_data.append((16, stride4, 7))
    config_data.append((17, order4, 7))
    config_data.append((18, size4, 7))
    config_data.append((19, stride5, 7))
    config_data.append((20, order5, 7))
    config_data.append((21, size5, 7))
    config_data.append((64, max_count, 7))

    for addr, data, feat in config_data:
        tester.configure(addr, data, feat)

    for i in range(depth):
        tester.write(i + 1)
    for i in range(depth):
        tester.write_and_observe(2 * i + 1)
    for i in range(depth, max_count):
        tester.observe(2 * i + 1)
    for i in range(depth):
        tester.write_and_observe(3 * i + 1)

    with tempfile.TemporaryDirectory() as tempdir:
        for genesis_verilog in glob.glob("genesis_verif/*.*"):
            shutil.copy(genesis_verilog, tempdir)
        tester.compile_and_run(directory=tempdir,
                               magma_output="coreir-verilog",
                               target="verilator",
                               flags=["-Wno-fatal"])


def db_basic(order0, order1, order2, order3, order4, order5,
             stride0, stride1, stride2, stride3, stride4, stride5,
             size0, size1, size2, size3, size4, size5,
             dimensionality,
             start_address=0,
             read_mode=0, manual_switch=1, arbitrary_addr=0):

    [Mem, tester] = make_memory_core()
    memory_size = 1024
    ranges = [size0, size1, size2, size3, size4, size5]
    strides = [stride0, stride1, stride2, stride3, stride4, stride5]
    tester.functional_model.config_db(memory_size, ranges, strides,
                                      start_address,
                                      manual_switch, dimensionality)

    mode = Mode.DB
    tile_enable = 1
    depth = 50
    config_data = []
    config_data.append((0, (depth << 3) | (tile_enable << 2) | mode.value, 0))
    config_data.append((0, read_mode, 7))
    config_data.append((1, arbitrary_addr, 7))
    config_data.append((2, start_address, 7))
    config_data.append((3, dimensionality, 7))
    config_data.append((4, stride0, 7))
    config_data.append((5, order0, 7))
    config_data.append((6, size0, 7))
    config_data.append((7, stride1, 7))
    config_data.append((8, order1, 7))
    config_data.append((9, size1, 7))
    config_data.append((10, stride2, 7))
    config_data.append((11, order2, 7))
    config_data.append((12, size2, 7))
    config_data.append((13, stride3, 7))
    config_data.append((14, order3, 7))
    config_data.append((15, size3, 7))
    config_data.append((16, stride4, 7))
    config_data.append((17, order4, 7))
    config_data.append((18, size4, 7))
    config_data.append((19, stride5, 7))
    config_data.append((20, order5, 7))
    config_data.append((21, size5, 7))

    for addr, data, feat in config_data:
        tester.configure(addr, data, feat)

    red = 0
    for i in range(27):
        tester.write((i + 1))

    tester.poke(Mem.clk_in, 0)
    tester.poke(Mem.switch_db, 1)
    tester.eval()
    tester.poke(Mem.clk_in, 1)
    tester.eval()
    tester.poke(Mem.clk_in, 0)
    tester.poke(Mem.switch_db, 0)
    tester.functional_model.switch()
    # pull based functional model hack
    if(read_mode == 0):
        tester.functional_model.read(0)
    tester.eval()

    for i in range(100):
        if(read_mode == 1):
            if(i == 47):
                tester.poke(Mem.switch_db, 1)
            if(i > 57):
                tester.read_and_write(i + 1)
            else:
                tester.write(i + 1)
            if(i == 47):
                tester.poke(Mem.switch_db, 0)
                tester.functional_model.switch()
                tester.eval()
        else:
            if(i == 47):
                tester.poke(Mem.switch_db, 1)

            # \_
            tester.poke(Mem.clk_in, 0)
            tester.poke(Mem.ren_in, 1)
            tester.poke(Mem.wen_in, 1)
            tester.poke(Mem.data_in, i + 1)
            tester.eval()

            # _/
            tester.poke(Mem.clk_in, 1)

            if(i == 47):
                tester.functional_model.write(0, i + 1)
                tester.functional_model.switch()
                tester.functional_model.read(0)
            else:
                tester.functional_model.read_and_write(0, i + 1)

            tester.eval()
            tester.poke(Mem.wen_in, 0)
            tester.poke(Mem.ren_in, 0)
            tester.eval()

            if(i == 47):
                tester.poke(Mem.switch_db, 0)
                tester.eval()

    with tempfile.TemporaryDirectory() as tempdir:
        for genesis_verilog in glob.glob("genesis_verif/*.*"):
            shutil.copy(genesis_verilog, tempdir)
        tester.compile_and_run(directory=tempdir,
                               magma_output="coreir-verilog",
                               target="verilator",
                               flags=["-Wno-fatal"])


def test_sram_magma(num_writes=20):

    [Mem, tester] = make_memory_core()
    mode = Mode.SRAM
    tile_enable = 1
    depth = 10
    config_data = []
    config_data.append((0, (depth << 3) | (tile_enable << 2) | mode.value, 0))
    for addr, data, feat in config_data:
        tester.configure(addr, data, feat)
    memory_size = 1024
    tester.functional_model.config_sram(memory_size)

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
        tester.write(data, addr)
        addrs.add(addr)

    # Read the values we wrote to make sure they are there
    for addr in addrs:
        print(str(addr))
        tester.read(addr)

    for i in range(num_writes):
        addr = get_fresh_addr(addrs)
        tester.read_and_write(random.randint(0, (1 << 10)), addr)
        tester.read(addr)

    with tempfile.TemporaryDirectory() as tempdir:
        for genesis_verilog in glob.glob("genesis_verif/*.*"):
            shutil.copy(genesis_verilog, tempdir)
        tester.compile_and_run(directory=tempdir,
                               magma_output="coreir-verilog",
                               target="verilator",
                               flags=["-Wno-fatal"])
