from memory_core import memory_core_genesis2
from memory_core.memory_core import gen_memory_core, Mode
from memory_core.memory_core_magma import MemCore
import glob
import os
import tempfile
import shutil
import fault
import random
from hwtypes import BitVector
from gemstone.common.testers import ResetTester, ConfigurationTester
from gemstone.generator.generator import Generator
from gemstone.common.testers import BasicTester


def make_memory_core():
    mem_core = MemCore(16, 16, 512, 2, 1)
    mem_circ = mem_core.circuit()
    # Setup functional model
    DATA_DEPTH = 1024
    DATA_WIDTH = 16
    MemFunctionalModel = gen_memory_core(DATA_WIDTH, DATA_DEPTH)
    mem_functional_model_inst = MemFunctionalModel()
    tester = MemoryCoreTester(mem_circ, clock=mem_circ.clk,
                              functional_model=mem_functional_model_inst)
    tester.poke(mem_circ.reset, 0)
    tester.step(1)
    tester.poke(mem_circ.reset, 1)
    tester.step(1)
    tester.reset()
    return [mem_circ, tester, mem_core]


class MemoryCoreTester(ResetTester, BasicTester):

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

    def write(self, data, addr=0):
        self.functional_model.write(addr, data)
        # \_
        self.poke(self._circuit.clk, 0)
        self.poke(self._circuit.wen_in, 1)
        self.poke(self._circuit.addr_in, addr)
        self.poke(self._circuit.data_in, data)
        self.eval()

        # _/
        self.poke(self._circuit.clk, 1)
        self.eval()
        self.poke(self._circuit.wen_in, 0)

    def write_and_observe(self, data, addr=0):
        self.functional_model.read(addr)
        self.functional_model.write(addr, data)
        self.eval()
        # \_
        self.poke(self._circuit.clk, 0)
        self.poke(self._circuit.wen_in, 1)
        self.poke(self._circuit.addr_in, addr)
        self.poke(self._circuit.data_in, data)
        self.eval()

        # _/
        self.poke(self._circuit.clk, 1)

    def observe(self, addr=0):
        self.functional_model.read(addr)
        self.eval()
        # \_
        self.poke(self._circuit.clk, 0)
        self.poke(self._circuit.wen_in, 1)
        self.poke(self._circuit.addr_in, addr)
        self.eval()

        # _/
        self.poke(self._circuit.clk, 1)

    def read(self, addr=0):
        # \_
        self.poke(self._circuit.clk, 0)
        self.poke(self._circuit.wen_in, 0)
        self.poke(self._circuit.addr_in, addr)
        self.poke(self._circuit.ren_in, 1)
        self.eval()

        # _/
        self.poke(self._circuit.clk, 1)
        self.eval()
        self.poke(self._circuit.ren_in, 0)

        self.poke(self._circuit.clk, 0)
        self.eval()

        self.poke(self._circuit.clk, 1)

        self.functional_model.read(addr)
        self.eval()
        # Don't expect anything after for now
        self.functional_model.data_out = fault.AnyValue

    def read_and_write(self, data, addr=0):
        # \_
        self.poke(self._circuit.clk, 0)
        self.poke(self._circuit.ren_in, 1)
        self.poke(self._circuit.wen_in, 1)
        self.poke(self._circuit.addr_in, addr)
        self.poke(self._circuit.data_in, data)
        self.eval()

        # _/
        self.poke(self._circuit.clk, 1)
        self.functional_model.read_and_write(addr, data)
        self.eval()
        self.poke(self._circuit.wen_in, 0)
        self.poke(self._circuit.ren_in, 0)
        self.eval()


def test_passthru_fifo(depth=50, read_cadence=2):
    # Regular Bootstrap
    [Mem, tester, MCore] = make_memory_core()
    mode = Mode.FIFO
    tile_en = 1
    config_data = []
    config_data.append((MCore.get_reg_index("depth"), depth, 0))
    config_data.append((MCore.get_reg_index("tile_en"), tile_en, 0))
    config_data.append((MCore.get_reg_index("mode"), mode.value, 0))
    tester.functional_model.config_fifo(depth)
    # Configure
    for addr, data, feat in config_data:
        tester.configure(addr, data, feat)
    # for i in range(27):
    #    tester.write(i + 1)

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
    [Mem, tester, MCore] = make_memory_core()
    mode = Mode.FIFO
    tile_en = 1
    config_data = []
    config_data.append((MCore.get_reg_index("depth"), depth, 0))
    config_data.append((MCore.get_reg_index("tile_en"), tile_en, 0))
    config_data.append((MCore.get_reg_index("mode"), mode.value, 0))
    # Configure the functional model in much the same way as the actual device
    tester.functional_model.config_fifo(depth)
    for addr, data, feat in config_data:
        tester.configure(addr, data, feat)

    for i in range(10):
        for i in range(depth):
            tester.write(random.randint(1, 101))
        for i in range(depth):
            tester.read()

    with tempfile.TemporaryDirectory() as tempdir:
        for genesis_verilog in glob.glob("genesis_verif/*.*"):
            shutil.copy(genesis_verilog, tempdir)
        tester.compile_and_run(directory=tempdir,
                               magma_output="coreir-verilog",
                               target="verilator",
                               flags=["-Wno-fatal"])


def test_general_fifo():
    fifo(50, 6)


def fifo(depth=50, read_cadence=2):
    [Mem, tester, MCore] = make_memory_core()
    mode = Mode.FIFO
    tile_en = 1
    config_data = []
    config_data.append((MCore.get_reg_index("depth"), depth, 0))
    config_data.append((MCore.get_reg_index("tile_en"), tile_en, 0))
    config_data.append((MCore.get_reg_index("mode"), mode.value, 0))
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
    db_basic(1, 3, 9, 0, 0, 0,
             3, 3, 3, 1, 1, 1,
             3)


def test_db_long_read():
    # More advanced access
    db_basic(1, 3, 1, 3, 9, 0,
             2, 2, 2, 2, 3, 1,
             5)


def test_db_read_mode():
    # Test read mode
    db_basic(1, 3, 9, 0, 0, 0,
             3, 3, 3, 1, 1, 1,
             3,
             0,
             1)


def test_db_arbitrary_rw_addr():

    [Mem, tester, MCore] = make_memory_core()
    memory_size = 1024
    ranges = [1, 1, 1, 1, 1, 1]
    strides = [1, 1, 1, 1, 1, 1]
    tester.functional_model.config_db(memory_size, ranges, strides,
                                      0, 1, 3, 1)

    read_mode = 1
    arbitrary_addr = 1
    mode = Mode.DB
    tile_en = 1
    depth = 130
    config_data = []
    config_data.append((MCore.get_reg_index("depth"), depth, 0))
    config_data.append((MCore.get_reg_index("tile_en"), tile_en, 0))
    config_data.append((MCore.get_reg_index("mode"), mode.value, 0))
    config_data.append((MCore.get_reg_index("read_mode"),
                        read_mode, 0))
    config_data.append((MCore.get_reg_index("arbitrary_addr"),
                        arbitrary_addr, 0))

    for addr, data, feat in config_data:
        tester.configure(addr, data, feat)

    for i in range(100):
        tester.write((i + 1))

    tester.poke(Mem.clk, 0)
    tester.poke(Mem.switch_db, 1)
    tester.eval()
    tester.poke(Mem.clk, 1)
    tester.eval()
    tester.poke(Mem.clk, 0)
    tester.poke(Mem.switch_db, 0)
    tester.functional_model.switch()

    for i in range(100):
        randaddr = random.randint(0, 99)
        tester.read_and_write(i + 1, randaddr)

    tester.poke(Mem.clk, 0)
    tester.poke(Mem.switch_db, 1)
    tester.functional_model.data_out = fault.AnyValue
    tester.eval()
    tester.poke(Mem.clk, 1)
    tester.eval()
    tester.poke(Mem.clk, 0)
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

    [Mem, tester, MCore] = make_memory_core()
    memory_size = 1024
    ranges = [1, 1, 1, 1, 1, 1]
    strides = [1, 1, 1, 1, 1, 1]
    tester.functional_model.config_db(memory_size, ranges, strides,
                                      0, 1, 3, 1)

    read_mode = 1
    arbitrary_addr = 1
    mode = Mode.DB
    tile_en = 1
    depth = 130

    config_data = []
    config_data.append((MCore.get_reg_index("depth"), depth, 0))
    config_data.append((MCore.get_reg_index("tile_en"), tile_en, 0))
    config_data.append((MCore.get_reg_index("mode"), mode.value, 0))
    config_data.append((MCore.get_reg_index("read_mode"), read_mode, 0))
    config_data.append((MCore.get_reg_index("arbitrary_addr"),
                        arbitrary_addr, 0))
    for addr, data, feat in config_data:
        tester.configure(addr, data, feat)

    for i in range(100):
        tester.write((i + 1))

    tester.poke(Mem.clk, 0)
    tester.poke(Mem.switch_db, 1)
    tester.eval()
    tester.poke(Mem.clk, 1)
    tester.eval()
    tester.poke(Mem.clk, 0)
    tester.poke(Mem.switch_db, 0)
    tester.functional_model.switch()
    tester.functional_model.data_out = fault.AnyValue

    for i in range(100):
        randaddr = random.randint(0, 99)
        tester.read(randaddr)

    for i in range(100):
        tester.write((i + 1))

    tester.poke(Mem.clk, 0)
    tester.poke(Mem.switch_db, 1)
    tester.eval()
    tester.poke(Mem.clk, 1)
    tester.eval()
    tester.poke(Mem.clk, 0)
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
                               flags=["-Wno-fatal"])


def test_db_auto():
    db_auto(1, 3, 9, 0, 0, 0,
            3, 3, 3, 1, 1, 1,
            3, 27)


def test_db_auto2():
    db_auto(1, 3, 1, 3, 9, 0,
            2, 2, 2, 2, 3, 1,
            5, 27)


def db_auto(stride_0, stride_1, stride_2, stride_3, stride_4, stride_5,
            range_0, range_1, range_2, range_3, range_4, range_5,
            dimensionality, input_size,
            starting_addr=0,
            read_mode=0, manual_switch=0, arbitrary_addr=0):

    [Mem, tester, MCore] = make_memory_core()
    iter_cnt = range_0 * range_1 * range_2 * range_3 * range_4 * range_5
    depth = input_size
    ranges = [range_0, range_1, range_2, range_3, range_4, range_5]
    strides = [stride_0, stride_1, stride_2, stride_3, stride_4, stride_5]
    tester.functional_model.config_db(depth, ranges, strides,
                                      starting_addr,
                                      manual_switch, dimensionality)
    # Assumes all ranges are 1 minimally

    mode = Mode.DB
    tile_en = 1
    config_data = []
    config_data.append((MCore.get_reg_index("depth"), depth, 0))
    config_data.append((MCore.get_reg_index("tile_en"), tile_en, 0))
    config_data.append((MCore.get_reg_index("mode"), mode.value, 0))
    config_data.append((MCore.get_reg_index("read_mode"),
                        read_mode, 0))
    config_data.append((MCore.get_reg_index("arbitrary_addr"),
                        arbitrary_addr, 0))
    config_data.append((MCore.get_reg_index("starting_addr"),
                        starting_addr, 0))
    config_data.append((MCore.get_reg_index("dimensionality"),
                        dimensionality, 0))
    config_data.append((MCore.get_reg_index("stride_0"), stride_0, 0))
    config_data.append((MCore.get_reg_index("stride_1"), stride_1, 0))
    config_data.append((MCore.get_reg_index("stride_2"), stride_2, 0))
    config_data.append((MCore.get_reg_index("stride_3"), stride_3, 0))
    config_data.append((MCore.get_reg_index("stride_4"), stride_4, 0))
    config_data.append((MCore.get_reg_index("stride_5"), stride_5, 0))
    config_data.append((MCore.get_reg_index("range_0"), range_0, 0))
    config_data.append((MCore.get_reg_index("range_1"), range_1, 0))
    config_data.append((MCore.get_reg_index("range_2"), range_2, 0))
    config_data.append((MCore.get_reg_index("range_3"), range_3, 0))
    config_data.append((MCore.get_reg_index("range_4"), range_4, 0))
    config_data.append((MCore.get_reg_index("range_5"), range_5, 0))
    config_data.append((MCore.get_reg_index("iter_cnt"), iter_cnt, 0))
    for addr, data, feat in config_data:
        tester.configure(addr, data, feat)

    for i in range(depth):
        tester.write(i + 1)
    for i in range(depth):
        tester.write_and_observe(2 * i + 1)
    for i in range(depth, iter_cnt):
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


def db_basic(stride_0, stride_1, stride_2, stride_3, stride_4, stride_5,
             range_0, range_1, range_2, range_3, range_4, range_5,
             dimensionality,
             starting_addr=0,
             read_mode=0, manual_switch=1, arbitrary_addr=0):

    [Mem, tester, MCore] = make_memory_core()
    memory_size = 1024
    ranges = [range_0, range_1, range_2, range_3, range_4, range_5]
    strides = [stride_0, stride_1, stride_2, stride_3, stride_4, stride_5]
    tester.functional_model.config_db(memory_size, ranges, strides,
                                      starting_addr,
                                      manual_switch, dimensionality)

    mode = Mode.DB
    tile_en = 1
    depth = 50
    config_data = []

    config_data.append((MCore.get_reg_index("depth"), depth, 0))
    config_data.append((MCore.get_reg_index("tile_en"), tile_en, 0))
    config_data.append((MCore.get_reg_index("mode"), mode.value, 0))
    config_data.append((MCore.get_reg_index("read_mode"), read_mode, 0))
    config_data.append((MCore.get_reg_index("arbitrary_addr"),
                        arbitrary_addr, 0))
    config_data.append((MCore.get_reg_index("starting_addr"),
                        starting_addr, 0))
    config_data.append((MCore.get_reg_index("dimensionality"),
                        dimensionality, 0))
    config_data.append((MCore.get_reg_index("stride_0"), stride_0, 0))
    config_data.append((MCore.get_reg_index("stride_1"), stride_1, 0))
    config_data.append((MCore.get_reg_index("stride_2"), stride_2, 0))
    config_data.append((MCore.get_reg_index("stride_3"), stride_3, 0))
    config_data.append((MCore.get_reg_index("stride_4"), stride_4, 0))
    config_data.append((MCore.get_reg_index("stride_5"), stride_5, 0))
    config_data.append((MCore.get_reg_index("range_0"), range_0, 0))
    config_data.append((MCore.get_reg_index("range_1"), range_1, 0))
    config_data.append((MCore.get_reg_index("range_2"), range_2, 0))
    config_data.append((MCore.get_reg_index("range_3"), range_3, 0))
    config_data.append((MCore.get_reg_index("range_4"), range_4, 0))
    config_data.append((MCore.get_reg_index("range_5"), range_5, 0))
    for addr, data, feat in config_data:
        tester.configure(addr, data, feat)

    red = 0
    for i in range(27):
        tester.write((i + 1))

    tester.poke(Mem.clk, 0)
    tester.poke(Mem.switch_db, 1)
    tester.eval()
    tester.poke(Mem.clk, 1)
    tester.eval()
    tester.poke(Mem.clk, 0)
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
            tester.poke(Mem.clk, 0)
            tester.poke(Mem.ren_in, 1)
            tester.poke(Mem.wen_in, 1)
            tester.poke(Mem.data_in, i + 1)
            tester.eval()

            # _/
            tester.poke(Mem.clk, 1)

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


def test_sram_magma(num_writes=500):

    [Mem, tester, MCore] = make_memory_core()
    mode = Mode.SRAM
    tile_en = 1
    depth = num_writes
    config_data = []
    config_data.append((MCore.get_reg_index("depth"), depth, 0))
    config_data.append((MCore.get_reg_index("tile_en"), tile_en, 0))
    config_data.append((MCore.get_reg_index("mode"), mode.value, 0))
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
