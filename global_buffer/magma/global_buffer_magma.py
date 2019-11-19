import magma as m
import mantle
from gemstone.generator.generator import Generator
from gemstone.generator.from_magma import FromMagma
from gemstone.generator.const import Const
from gemstone.common.mux_wrapper import MuxWrapper
from global_buffer.magma.io_controller_magma import IoController
from global_buffer.magma.memory_bank_magma import MemoryBank

GLB_ADDR_WIDTH = 32
BANK_ADDR_WIDTH = 17
BANK_DATA_WIDTH = 64

class GlobalBuffer(Generator):
    def __init__(self, num_banks, num_io_channels):

        self.num_banks = num_banks
        self.num_io_channels = num_io_channels
        self.banks_per_io = int(num_banks / num_io_channels)
        super().__init__()

        self.add_ports(
            clk=m.In(m.Clock),
            reset=m.In(m.AsyncReset),
        )

    def name(self):
        return f"GlobalBuffer_{self.num_banks}_{self.num_io_channels}"


    io_ctrl = IoController(self.num_banks, self.num_io_channels)
    memory_bank = [None]*self.num_banks
    for i in range(self.num_banks):
        memory_bank[i] = MemoryBank(64, 17, 32)

global_buffer = GlobalBuffer(32, 8)
m.compile("global_buffer", global_buffer.circuit(), output="coreir-verilog")
