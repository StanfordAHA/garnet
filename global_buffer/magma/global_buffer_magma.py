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
GLB_CFG_ADDR_WIDTH = 12
GLB_CFG_DATA_WIDTH = 12

class GlobalBuffer(Generator):
    def __init__(self, num_banks, num_io_channels):

        self.num_banks = num_banks
        self.num_io_channels = num_io_channels
        self.banks_per_io = int(num_banks / num_io_channels)
        super().__init__()

        self.add_ports(
            clk=m.In(m.Clock),
            reset=m.In(m.AsyncReset),

            # glc
            stall=m.In(m.Bits[1]),
            cgra_start_pulse=m.In(m.Bit),
            cgra_done_pulse=m.Out(m.Bit),
            # config_start_pulse=m.In(m.Bit),
            # config_done_pulse=m.Out(m.Bit),

            # cgra
            cgra_to_io_wr_en=m.In(m.Array[self.num_io_channels, m.Bit]),
            cgra_to_io_rd_en=m.In(m.Array[self.num_io_channels, m.Bit]),
            io_to_cgra_rd_data_valid=m.Out(m.Array[self.num_io_channels, m.Bit]),
            cgra_to_io_wr_data=m.In(m.Array[self.num_io_channels, m.Bits[16]]),
            io_to_cgra_rd_data=m.Out(m.Array[self.num_io_channels, m.Bits[16]]),
            cgra_to_io_addr_high=m.In(m.Array[self.num_io_channels, m.Bits[16]]),
            cgra_to_io_addr_low=m.In(m.Array[self.num_io_channels, m.Bits[16]]),

            # glc
            # glb_to_cgra_cfg_wr=m.Out(m.Array[self.num_cfg_channels, m.Bit]),
            # glb_to_cgra_cfg_rd=m.Out(m.Array[self.num_cfg_channels, m.Bit]),
            # glb_to_cgra_cfg_addr=m.Out(m.Array[self.num_cfg_channels, m.Bits[32]]),
            # glb_to_cgra_cfg_data=m.Out(m.Array[self.num_cfg_channels, m.Bits[32]]),

            # glb configuration
            glb_config_wr=m.In(m.Bit),
            glb_config_rd=m.In(m.Bit),
            glb_config_addr=m.In(m.Bits[GLB_CFG_ADDR_WIDTH]),
            glb_config_wr_data=m.In(m.Bits[GLB_CFG_DATA_WIDTH]),
            glb_config_rd_data=m.Out(m.Bits[GLB_CFG_DATA_WIDTH]),
        )

        # host
        # TODO

        # memory bank
        io_to_bank_wr_en=[m.Bits[1]]*self.num_banks
        io_to_bank_wr_data=[m.Bits[BANK_DATA_WIDTH]]*self.num_banks
        io_to_bank_wr_data_bit_sel=[m.Bits[BANK_DATA_WIDTH]]*self.num_banks
        io_to_bank_wr_addr=[m.Bits[BANK_ADDR_WIDTH]]*self.num_banks
        io_to_bank_rd_en=[m.Bits[1]]*self.num_banks
        io_to_bank_rd_addr=[m.Bits[BANK_ADDR_WIDTH]]*self.num_banks
        bank_to_io_rd_data=[m.Bits[BANK_DATA_WIDTH]]*self.num_banks
        memory_bank = [None]*self.num_banks
        for i in range(self.num_banks):
            memory_bank[i] = MemoryBank(64, 17, 32)
            io_to_bank_wr_en[i]=memory_bank[i].ports.cgra_wr_en
            io_to_bank_wr_data[i]=memory_bank[i].ports.cgra_wr_data
            io_to_bank_wr_data_bit_sel[i]=memory_bank[i].ports.cgra_wr_data_bit_sel
            io_to_bank_wr_addr[i]=memory_bank[i].ports.cgra_wr_addr
            io_to_bank_rd_en[i]=memory_bank[i].ports.cgra_rd_en
            bank_to_io_rd_data[i]=memory_bank[i].ports.cgra_rd_data
            io_to_bank_rd_addr[i]=memory_bank[i].ports.cgra_rd_addr

        # io_controller
        io_ctrl = IoController(self.num_banks, self.num_io_channels)
        self.wire(self.ports.clk, io_ctrl.ports.clk)
        self.wire(self.ports.reset, io_ctrl.ports.reset)
        self.wire(self.ports.stall, io_ctrl.ports.stall)
        self.wire(self.ports.cgra_start_pulse, io_ctrl.ports.cgra_start_pulse)
        self.wire(self.ports.cgra_done_pulse, io_ctrl.ports.cgra_done_pulse)

        # io_controller - bank wiring
        for i in range(self.num_banks):
            self.wire(io_ctrl.ports.io_to_bank_wr_en[i], io_to_bank_wr_en[i])
            self.wire(io_ctrl.ports.io_to_bank_wr_data[i], io_to_bank_wr_data[i])
            self.wire(io_ctrl.ports.io_to_bank_wr_data_bit_sel[i], io_to_bank_wr_data_bit_sel[i])
            self.wire(io_ctrl.ports.io_to_bank_wr_addr[i], io_to_bank_wr_addr[i])
            self.wire(io_ctrl.ports.io_to_bank_rd_en[i], io_to_bank_rd_en[i])
            self.wire(io_ctrl.ports.bank_to_io_rd_data[i], bank_to_io_rd_data[i])
            self.wire(io_ctrl.ports.io_to_bank_rd_addr[i], io_to_bank_rd_addr[i])

        # cgra ports
        self.wire(self.ports.cgra_to_io_wr_en, io_ctrl.ports.cgra_to_io_wr_en)
        self.wire(self.ports.cgra_to_io_rd_en, io_ctrl.ports.cgra_to_io_rd_en)
        self.wire(self.ports.io_to_cgra_rd_data_valid, io_ctrl.ports.io_to_cgra_rd_data_valid)
        self.wire(self.ports.cgra_to_io_wr_data, io_ctrl.ports.cgra_to_io_wr_data)
        self.wire(self.ports.io_to_cgra_rd_data, io_ctrl.ports.io_to_cgra_rd_data)
        self.wire(self.ports.cgra_to_io_addr_high, io_ctrl.ports.cgra_to_io_addr_high)
        self.wire(self.ports.cgra_to_io_addr_low, io_ctrl.ports.cgra_to_io_addr_low)

        # io_controller configuration wiring
        self.wire(self.ports.glb_config_wr, io_ctrl.ports.config_wr)
        self.wire(self.ports.glb_config_rd, io_ctrl.ports.config_rd)
        # TODO
        self.wire(self.ports.glb_config_addr, io_ctrl.ports.config_addr)
        self.wire(self.ports.glb_config_wr_data, io_ctrl.ports.config_wr_data)
        # TODO
        self.wire(self.ports.glb_config_rd_data, io_ctrl.ports.config_rd_data)

    def name(self):
        return f"GlobalBuffer_{self.num_banks}_{self.num_io_channels}"

global_buffer = GlobalBuffer(32, 8)
m.compile("global_buffer", global_buffer.circuit(), output="coreir-verilog")
