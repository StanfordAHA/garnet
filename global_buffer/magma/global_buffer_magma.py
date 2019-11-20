import magma as m
import mantle
from gemstone.generator.generator import Generator
from gemstone.generator.from_magma import FromMagma
from gemstone.generator.const import Const
from gemstone.common.mux_wrapper import MuxWrapper
from global_buffer.magma.io_controller_magma import IoController
from global_buffer.magma.host_bank_interconnect_magma import HostBankInterconnect
from global_buffer.magma.memory_bank_magma import MemoryBank

GLB_ADDR_WIDTH = 32
BANK_ADDR_WIDTH = 17
BANK_DATA_WIDTH = 64
GLB_CFG_ADDR_WIDTH = 12
GLB_CFG_DATA_WIDTH = 32
CFG_ADDR_WIDTH = 32

class GlobalBuffer(Generator):
    def __init__(self, num_banks, num_io_channels):

        self.num_banks = num_banks
        self.num_io_channels = num_io_channels
        self.banks_per_io = int(num_banks / num_io_channels)
        super().__init__()

        self.add_ports(
            clk=m.In(m.Clock),
            reset=m.In(m.AsyncReset),

            # host
            # host write
            host_wr_en=m.In(m.Bits[1]),
            host_wr_strb=m.In(m.Bits[int(BANK_DATA_WIDTH/8)]),
            host_wr_data=m.In(m.Bits[BANK_DATA_WIDTH]),
            host_wr_addr=m.In(m.Bits[GLB_ADDR_WIDTH]),

            # host read
            host_rd_en=m.In(m.Bits[1]),
            host_rd_addr=m.In(m.Bits[GLB_ADDR_WIDTH]),
            host_rd_data=m.Out(m.Bits[BANK_DATA_WIDTH]),

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

            # glb sram configuration
            glb_sram_config_wr=m.In(m.Bit),
            glb_sram_config_rd=m.In(m.Bit),
            glb_sram_config_addr=m.In(m.Bits[CFG_ADDR_WIDTH]),
            glb_sram_config_wr_data=m.In(m.Bits[GLB_CFG_DATA_WIDTH]),
            glb_sram_config_rd_data=m.Out(m.Bits[GLB_CFG_DATA_WIDTH]),

            # glb configuration
            glb_config_wr=m.In(m.Bit),
            glb_config_rd=m.In(m.Bit),
            glb_config_addr=m.In(m.Bits[GLB_CFG_ADDR_WIDTH]),
            glb_config_wr_data=m.In(m.Bits[GLB_CFG_DATA_WIDTH]),
            glb_config_rd_data=m.Out(m.Bits[GLB_CFG_DATA_WIDTH]),
        )

        # host
        host_bank_interconnect = HostBankInterconnect(self.num_banks)
        self.wire(self.ports.clk, host_bank_interconnect.ports.clk)
        self.wire(self.ports.reset, host_bank_interconnect.ports.reset)
        # host write
        self.wire(self.ports.host_wr_en, host_bank_interconnect.ports.host_wr_en)
        self.wire(self.ports.host_wr_strb, host_bank_interconnect.ports.host_wr_strb)
        self.wire(self.ports.host_wr_data, host_bank_interconnect.ports.host_wr_data)
        self.wire(self.ports.host_wr_addr, host_bank_interconnect.ports.host_wr_addr)

        # host read
        self.wire(self.ports.host_rd_en, host_bank_interconnect.ports.host_rd_en)
        self.wire(self.ports.host_rd_addr, host_bank_interconnect.ports.host_rd_addr)
        self.wire(self.ports.host_rd_data, host_bank_interconnect.ports.host_rd_data)

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

        # memory bank config
        glb_sram_config_en_bank=[m.Bit]*self.num_banks
        for i in range(self.num_banks):
            eq = FromMagma(mantle.DefineEQ(15))
            self.wire(Const(i), eq.ports.I0)
            self.wire(self.ports.glb_sram_config_addr[17:32], eq.ports.I1)
            glb_sram_config_en_bank[i]=eq.ports.O

        glb_sram_config_rd_data_bank=[m.Bits[32]]*self.num_banks
        for i in range(self.num_banks):
            self.wire(memory_bank[i].ports.config_en, glb_sram_config_en_bank[i])
            self.wire(memory_bank[i].ports.config_wr, self.ports.glb_sram_config_wr)
            self.wire(memory_bank[i].ports.config_rd, self.ports.glb_sram_config_rd)
            self.wire(memory_bank[i].ports.config_addr, self.ports.glb_sram_config_addr[0:BANK_ADDR_WIDTH])
            self.wire(memory_bank[i].ports.config_wr_data, self.ports.glb_sram_config_wr_data)
            glb_sram_config_rd_data_bank[i]=memory_bank[i].ports.config_rd_data

        mux = MuxWrapper(self.num_banks, 32,)
        for i in range(self.num_banks):
            self.wire(glb_sram_config_rd_data_bank[i], mux.ports.I[i])
        self.wire(self.ports.glb_sram_config_addr[BANK_ADDR_WIDTH:BANK_ADDR_WIDTH+5], mux.ports.S)
        self.wire(self.ports.glb_sram_config_rd_data, mux.ports.O)

        # host to bank
        for i in range(self.num_banks):
            self.wire(memory_bank[i].ports.host_wr_en, host_bank_interconnect.ports.host_to_bank_wr_en[i][0])
            self.wire(memory_bank[i].ports.host_wr_data, host_bank_interconnect.ports.host_to_bank_wr_data[i])
            self.wire(memory_bank[i].ports.host_wr_data_bit_sel, host_bank_interconnect.ports.host_to_bank_wr_data_bit_sel[i])
            self.wire(memory_bank[i].ports.host_wr_addr, host_bank_interconnect.ports.host_to_bank_wr_addr[i])
            self.wire(memory_bank[i].ports.host_rd_en, host_bank_interconnect.ports.host_to_bank_rd_en[i][0])
            self.wire(memory_bank[i].ports.host_rd_addr, host_bank_interconnect.ports.host_to_bank_rd_addr[i])
            self.wire(memory_bank[i].ports.host_rd_data, host_bank_interconnect.ports.bank_to_host_rd_data[i])
            # TODO cfg controller
            self.wire(memory_bank[i].ports.cfg_rd_en, Const(0))
            self.wire(memory_bank[i].ports.cfg_rd_addr, Const(0))

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

        # io controller config
        glb_config_en_io=[m.Bit]*self.num_banks
        eq = FromMagma(mantle.DefineEQ(2))
        self.wire(Const(1), eq.ports.I0)
        self.wire(self.ports.glb_config_addr[10:12], eq.ports.I1)
        glb_config_en_io=eq.ports.O

        # io_controller configuration wiring
        self.wire(glb_config_en_io, io_ctrl.ports.config_en)
        self.wire(self.ports.glb_config_wr, io_ctrl.ports.config_wr)
        self.wire(self.ports.glb_config_rd, io_ctrl.ports.config_rd)
        self.wire(self.ports.glb_config_addr[0:8], io_ctrl.ports.config_addr)
        self.wire(self.ports.glb_config_wr_data, io_ctrl.ports.config_wr_data)
        # TODO
        self.wire(self.ports.glb_config_rd_data, io_ctrl.ports.config_rd_data)

    def name(self):
        return f"GlobalBuffer_{self.num_banks}_{self.num_io_channels}"

global_buffer = GlobalBuffer(32, 8)
m.compile("global_buffer", global_buffer.circuit(), output="coreir-verilog")
