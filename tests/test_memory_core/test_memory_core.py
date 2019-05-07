from memory_core import memory_core_genesis2
from memory_core.memory_core import gen_memory_core, Mode
import glob
import os
import shutil
import fault
import random
from hwtypes import BitVector
from gemstone.common.testers import ResetTester, ConfigurationTester
from memory_core.memory_core_magma import MemCore
from gemstone.common.testers import BasicTester
import magma
import canal
import coreir
from gemstone.generator.generator import Generator

def bringup_tester():
  generator = memory_core_genesis2.memory_core_wrapper.generator(param_mapping=memory_core_genesis2.param_mapping)
  Mem = generator()
  for genesis_verilog in glob.glob("genesis_verif/*.v"):
    shutil.copy(genesis_verilog, "tests/test_memory_core/build")

  # Setup functional model
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
  return [Mem, tester]


class MemoryCoreTester(ResetTester, ConfigurationTester):
    def write(self, addr, data):
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

    def read(self, addr):
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

    def read_and_write(self, addr, data):
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
        # \_
        #self.poke(self._circuit.clk_in, 0)
        #self.eval()
        #self.poke(self._circuit.clk_in, 1)
        #self.eval()


def test_compile():
  # Setup functional model
  DATA_DEPTH = 1024
  DATA_WIDTH = 16
  mem_core = MemCore(16,16,512,2)
  circuit = mem_core.circuit()
  tester = fault.Tester(circuit, circuit.clk_in)
  tester.poke(circuit.reset, 1)
  tester.poke(circuit.reset, 0)
  tester.step(2)
  tester.poke(circuit.config_en_db, 1)
  tester.step(5)
  tester.poke(circuit.config_en_db, 0)
  tester.step(2)

  testdir = "tests/test_memory_core/build"
  for genesis_verilog in glob.glob("genesis_verif/*.*"):
                 shutil.copy(genesis_verilog, testdir)
  tester.compile_and_run(target="verilator",
                                magma_output="coreir-verilog",
                                directory=testdir,
                              flags=["-Wno-fatal --trace"])

def test_passthru_fifo(depth=50, read_cadence=2):

  [Mem, tester] = bringup_tester()
  mode = Mode.FIFO
  tile_enable = 1
  config_data = mode.value | (tile_enable << 2) | (depth << 3)
  config_addr = BitVector(0, 32)
  tester.configure(config_addr, BitVector(config_data, 32))
  tester.poke(Mem.config_en_fifo, 1)
  tester.poke(Mem.config_write, 1)
  tester.eval()
  # Configure
  tester.configure(BitVector(0,32), BitVector(1, 32))

  tester.poke(Mem.config_en, 0)
  tester.step()
  tester.poke(Mem.config_en_fifo,0)
  tester.poke(Mem.clk_in, 0)
  tester.poke(Mem.config_write, 0)
  tester.eval()

  tester.functional_model.config_fifo(depth)

  tester.read_and_write(0, 42)
  tester.read_and_write(0, 43)
  tester.read_and_write(0, 44)

  tester.compile_and_run(directory="tests/test_memory_core/build",
                           magma_output="verilog",
                           target="verilator",
                           flags=["-Wno-fatal --trace"])

def test_general_fifo():
  fifo(50, 6)

def fifo(depth=50, read_cadence=2):

  [Mem, tester] = bringup_tester()
  mode = Mode.FIFO
  tile_enable = 1
  config_data = mode.value | (tile_enable << 2) | (depth << 3)
  config_addr = BitVector(0, 32)
  tester.configure(config_addr, BitVector(config_data, 32))
  tester.poke(Mem.config_en_fifo, 1)
  tester.poke(Mem.config_write, 1)
  tester.eval()
  # Configure
  tester.configure(BitVector(0,32), BitVector(1, 32))

  tester.poke(Mem.config_en, 0)
  tester.step()
  tester.poke(Mem.config_en_fifo,0)
  tester.poke(Mem.clk_in, 0)
  tester.poke(Mem.config_write, 0)
  tester.eval()

  # Configure the functional model in much the same way as the actual device
  tester.functional_model.config_fifo(depth)

  read = 1
  switch = 0
  # do depth writes, then read
  for i in range(depth):
    if(i % read_cadence == 0):
      tester.read_and_write(0, i+1)
    else:
      tester.write(0,i+1)

  tester.compile_and_run(directory="tests/test_memory_core/build",
                           magma_output="verilog",
                           target="verilator",
                           flags=["-Wno-fatal --trace"])

def test_db_long_read():
  # Basic access
  db_basic( 0, 1, 2, 3, 4, 5,
            1, 3, 9, 0, 0, 0,
            3, 3, 3, 1, 1, 1,
            3)
def test_db_long_read2():
  # More advanced access
  db_basic( 0, 1, 2, 3, 4, 5,
            1, 3, 1, 3, 9, 0,
            2, 2, 2, 2, 3, 1,
            5)



def test_db_read_mode():
  # Test read mode
  db_basic( 0, 1, 2, 3, 4, 5,
            1, 3, 9, 0, 0, 0,
            3, 3, 3, 1, 1, 1,
            3,
            0,
            1)

def db_basic( order0, order1, order2, order3, order4, order5,
              stride0, stride1, stride2, stride3, stride4, stride5,
              size0, size1, size2, size3, size4, size5,
              dimensionality,
              start_address=0,
              read_mode=0, manual_switch=1):

  [Mem, tester] = bringup_tester()

  mode = Mode.DB # DB
  tile_enable = 1
  depth = 50
  config_data = 3 | (tile_enable << 2) | (depth << 3)
  config_addr = BitVector(0, 32)
  tester.configure(config_addr, BitVector(config_data, 32))

  ranges = [size0, size1, size2, size3, size4, size5]
  strides = [stride0, stride1, stride2, stride3, stride4, stride5]
  tester.functional_model.config_db(1024, ranges, strides, start_address, manual_switch, dimensionality)


  # Now configure the db - then write 1-27
  tester.poke(Mem.config_en, 0)
  tester.poke(Mem.config_en_db, 1)
  tester.poke(Mem.config_write, 1)
  tester.configure(BitVector(1,32), BitVector(stride0, 32))
  tester.configure(BitVector(2,32), BitVector(order0, 32))
  tester.configure(BitVector(3,32), BitVector(size0, 32))
  tester.configure(BitVector(4,32), BitVector(stride1, 32))
  tester.configure(BitVector(5,32), BitVector(order1, 32))
  tester.configure(BitVector(6,32), BitVector(size1, 32))
  tester.configure(BitVector(7,32), BitVector(stride2, 32))
  tester.configure(BitVector(8,32), BitVector(order2, 32))
  tester.configure(BitVector(9,32), BitVector(size2, 32))
  tester.configure(BitVector(10,32), BitVector(stride3, 32))
  tester.configure(BitVector(11,32), BitVector(order3, 32))
  tester.configure(BitVector(12,32), BitVector(size3, 32))
  tester.configure(BitVector(13,32), BitVector(stride4, 32))
  tester.configure(BitVector(14,32), BitVector(order4, 32))
  tester.configure(BitVector(15,32), BitVector(size4, 32))
  tester.configure(BitVector(16,32), BitVector(stride5, 32))
  tester.configure(BitVector(17,32), BitVector(order5, 32))
  tester.configure(BitVector(18, 32), BitVector(size5, 32))
  tester.configure(BitVector(666, 32), BitVector(start_address, 32))
  tester.configure(BitVector(668,32), BitVector(dimensionality, 32))
  if(read_mode == 1):
    tester.configure(BitVector(667, 32), BitVector(1, 32))

  tester.poke(Mem.config_en, 0)
  tester.step()

  tester.poke(Mem.config_en_db,0)
  tester.poke(Mem.clk_in, 0)
  tester.eval()

  red = 0
  for i in range(27):
    tester.write(0,(i+1))

  tester.poke(Mem.clk_in,0)
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
    if(read_mode==1):
      if(i == 47):
        tester.poke(Mem.switch_db,1)
      if(i > 57):
        tester.read_and_write(0,i+1)
      else:
        tester.write(0,i+1)
      if(i == 47):
        tester.poke(Mem.switch_db,0)
        tester.functional_model.switch()
        tester.eval()
    else:
      if(i == 47):
        tester.poke(Mem.switch_db,1)

      # \_
      tester.poke(Mem.clk_in, 0)
      tester.poke(Mem.ren_in, 1)
      tester.poke(Mem.wen_in, 1)
      tester.poke(Mem.data_in, i+1)
      tester.eval()

      # _/
      tester.poke(Mem.clk_in, 1)

      if(i == 47):
        tester.functional_model.write(0, i+1)
        tester.functional_model.switch()
        tester.functional_model.read(0)
      else:
        tester.functional_model.read_and_write(0, i+1)
      tester.eval()
      tester.poke(Mem.wen_in, 0)
      tester.poke(Mem.ren_in, 0)
      tester.eval()

      if(i ==47):
        tester.poke(Mem.switch_db,0)
        tester.eval()


  tester.compile_and_run(directory="tests/test_memory_core/build",
                           magma_output="verilog",
                           target="verilator",
                           flags=["-Wno-fatal --trace"])


def test_sram_basic(num_writes=1000):

    [Mem, tester] = bringup_tester()
    mode = Mode.SRAM
    tile_enable = 1
    depth = 8
    config_data = mode.value | (tile_enable << 2) | (depth << 3)
    config_addr = BitVector(0, 32)
    tester.configure(config_addr, BitVector(config_data, 32))
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
        tester.write(addr, data)
        addrs.add(addr)

    # Read the values we wrote to make sure they are there
    for addr in addrs:
        print(str(addr))
        tester.read(addr)

    for i in range(num_writes):
        addr = get_fresh_addr(addrs)
        tester.read_and_write(addr, random.randint(0, (1 << 10)))
        tester.read(addr)

    tester.compile_and_run(directory="tests/test_memory_core/build",
                           magma_output="verilog",
                           target="verilator",
                           flags=["-Wno-fatal --trace"])
