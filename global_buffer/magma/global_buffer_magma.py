import magma as m
import mantle
from gemstone.generator.generator import Generator
from gemstone.generator.from_magma import FromMagma
from gemstone.generator.const import Const
from gemstone.common.mux_wrapper import MuxWrapper
from gemstone.common.mux_with_default import MuxWithDefaultWrapper
from global_buffer.magma.io_controller_magma import IoController
from global_buffer.magma.cfg_controller_magma import CfgController
from global_buffer.magma.host_bank_interconnect_magma import HostBankInterconnect
from global_buffer.magma.memory_bank_magma import MemoryBank

GLB_ADDR_WIDTH = 32
BANK_ADDR_WIDTH = 17
BANK_DATA_WIDTH = 64
GLB_CFG_ADDR_WIDTH = 12
GLB_CFG_DATA_WIDTH = 32
CFG_ADDR_WIDTH = 32

class GlobalBuffer(Generator):
    def __init__(self, num_banks, num_io_channels, num_cfg_channels):

        self.num_banks = num_banks
        self.num_io_channels = num_io_channels
        self.num_cfg_channels = num_cfg_channels
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
            config_start_pulse=m.In(m.Bit),
            config_done_pulse=m.Out(m.Bit),

            # cgra
            cgra_to_io_wr_en=m.In(m.Array[self.num_io_channels, m.Bit]),
            cgra_to_io_rd_en=m.In(m.Array[self.num_io_channels, m.Bit]),
            io_to_cgra_rd_data_valid=m.Out(m.Array[self.num_io_channels, m.Bit]),
            cgra_to_io_wr_data=m.In(m.Array[self.num_io_channels, m.Bits[16]]),
            io_to_cgra_rd_data=m.Out(m.Array[self.num_io_channels, m.Bits[16]]),
            cgra_to_io_addr_high=m.In(m.Array[self.num_io_channels, m.Bits[16]]),
            cgra_to_io_addr_low=m.In(m.Array[self.num_io_channels, m.Bits[16]]),

            # glc
            glc_to_cgra_cfg_wr=m.In(m.Bit),
            glc_to_cgra_cfg_rd=m.In(m.Bit),
            glc_to_cgra_cfg_addr=m.In(m.Bits[32]),
            glc_to_cgra_cfg_data=m.In(m.Bits[32]),

            # glb
            glb_to_cgra_cfg_wr=m.Out(m.Array[self.num_cfg_channels, m.Bit]),
            glb_to_cgra_cfg_rd=m.Out(m.Array[self.num_cfg_channels, m.Bit]),
            glb_to_cgra_cfg_addr=m.Out(m.Array[self.num_cfg_channels, m.Bits[32]]),
            glb_to_cgra_cfg_data=m.Out(m.Array[self.num_cfg_channels, m.Bits[32]]),

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
        self.host_bank_interconnect = HostBankInterconnect(self.num_banks, self.banks_per_io)
        self.wire(self.ports.clk, self.host_bank_interconnect.ports.clk)
        self.wire(self.ports.reset, self.host_bank_interconnect.ports.reset)
        # host write
        self.wire(self.ports.host_wr_en, self.host_bank_interconnect.ports.host_wr_en)
        self.wire(self.ports.host_wr_strb, self.host_bank_interconnect.ports.host_wr_strb)
        self.wire(self.ports.host_wr_data, self.host_bank_interconnect.ports.host_wr_data)
        self.wire(self.ports.host_wr_addr, self.host_bank_interconnect.ports.host_wr_addr)

        # host read
        self.wire(self.ports.host_rd_en, self.host_bank_interconnect.ports.host_rd_en)
        self.wire(self.ports.host_rd_addr, self.host_bank_interconnect.ports.host_rd_addr)
        self.wire(self.ports.host_rd_data, self.host_bank_interconnect.ports.host_rd_data)

        # memory bank
        io_to_bank_wr_en=[m.Bits[1]]*self.num_banks
        io_to_bank_wr_data=[m.Bits[BANK_DATA_WIDTH]]*self.num_banks
        io_to_bank_wr_data_bit_sel=[m.Bits[BANK_DATA_WIDTH]]*self.num_banks
        io_to_bank_wr_addr=[m.Bits[BANK_ADDR_WIDTH]]*self.num_banks
        io_to_bank_rd_en=[m.Bits[1]]*self.num_banks
        io_to_bank_rd_addr=[m.Bits[BANK_ADDR_WIDTH]]*self.num_banks
        bank_to_io_rd_data=[m.Bits[BANK_DATA_WIDTH]]*self.num_banks
        cfg_to_bank_rd_en=[m.Bits[1]]*self.num_banks
        cfg_to_bank_rd_addr=[m.Bits[BANK_ADDR_WIDTH]]*self.num_banks
        bank_to_cfg_rd_data=[m.Bits[BANK_DATA_WIDTH]]*self.num_banks
        self.memory_bank = [None]*self.num_banks
        for i in range(self.num_banks):
            self.memory_bank[i] = MemoryBank(64, 17, 32)
            io_to_bank_wr_en[i]=self.memory_bank[i].ports.cgra_wr_en
            io_to_bank_wr_data[i]=self.memory_bank[i].ports.cgra_wr_data
            io_to_bank_wr_data_bit_sel[i]=self.memory_bank[i].ports.cgra_wr_data_bit_sel
            io_to_bank_wr_addr[i]=self.memory_bank[i].ports.cgra_wr_addr
            io_to_bank_rd_en[i]=self.memory_bank[i].ports.cgra_rd_en
            bank_to_io_rd_data[i]=self.memory_bank[i].ports.cgra_rd_data
            io_to_bank_rd_addr[i]=self.memory_bank[i].ports.cgra_rd_addr
            cfg_to_bank_rd_en[i]=self.memory_bank[i].ports.cfg_rd_en
            cfg_to_bank_rd_addr[i]=self.memory_bank[i].ports.cfg_rd_addr
            bank_to_cfg_rd_data[i]=self.memory_bank[i].ports.cfg_rd_data

        # memory bank config
        glb_sram_config_en_bank=[m.Bit]*self.num_banks
        eq_def = mantle.DefineEQ(15)
        for i in range(self.num_banks):
            eq = FromMagma(eq_def)
            self.wire(Const(i), eq.ports.I0)
            self.wire(self.ports.glb_sram_config_addr[17:32], eq.ports.I1)
            glb_sram_config_en_bank[i]=eq.ports.O

        glb_sram_config_rd_data_bank=[m.Bits[32]]*self.num_banks
        for i in range(self.num_banks):
            self.wire(self.memory_bank[i].ports.config_en, glb_sram_config_en_bank[i])
            self.wire(self.memory_bank[i].ports.config_wr, self.ports.glb_sram_config_wr)
            self.wire(self.memory_bank[i].ports.config_rd, self.ports.glb_sram_config_rd)
            self.wire(self.memory_bank[i].ports.config_addr, self.ports.glb_sram_config_addr[0:BANK_ADDR_WIDTH])
            self.wire(self.memory_bank[i].ports.config_wr_data, self.ports.glb_sram_config_wr_data)
            glb_sram_config_rd_data_bank[i]=self.memory_bank[i].ports.config_rd_data

        mux = MuxWrapper(self.num_banks, 32,)
        for i in range(self.num_banks):
            self.wire(glb_sram_config_rd_data_bank[i], mux.ports.I[i])
        self.wire(self.ports.glb_sram_config_addr[BANK_ADDR_WIDTH:BANK_ADDR_WIDTH+5], mux.ports.S)
        self.wire(self.ports.glb_sram_config_rd_data, mux.ports.O)

        # host to bank
        for i in range(self.num_banks):
            self.wire(self.memory_bank[i].ports.host_wr_en, self.host_bank_interconnect.ports.host_to_bank_wr_en[i][0])
            self.wire(self.memory_bank[i].ports.host_wr_data, self.host_bank_interconnect.ports.host_to_bank_wr_data[i])
            self.wire(self.memory_bank[i].ports.host_wr_data_bit_sel, self.host_bank_interconnect.ports.host_to_bank_wr_data_bit_sel[i])
            self.wire(self.memory_bank[i].ports.host_wr_addr, self.host_bank_interconnect.ports.host_to_bank_wr_addr[i])
            self.wire(self.memory_bank[i].ports.host_rd_en, self.host_bank_interconnect.ports.host_to_bank_rd_en[i][0])
            self.wire(self.memory_bank[i].ports.host_rd_addr, self.host_bank_interconnect.ports.host_to_bank_rd_addr[i])
            self.wire(self.memory_bank[i].ports.host_rd_data, self.host_bank_interconnect.ports.bank_to_host_rd_data[i])

        # io_controller
        self.io_ctrl = IoController(self.num_banks, self.num_io_channels)
        self.wire(self.ports.clk, self.io_ctrl.ports.clk)
        self.wire(self.ports.reset, self.io_ctrl.ports.reset)
        self.wire(self.ports.stall, self.io_ctrl.ports.stall)
        self.wire(self.ports.cgra_start_pulse, self.io_ctrl.ports.cgra_start_pulse)
        self.wire(self.ports.cgra_done_pulse, self.io_ctrl.ports.cgra_done_pulse)

        # io_controller - bank wiring
        for i in range(self.num_banks):
            self.wire(self.io_ctrl.ports.io_to_bank_wr_en[i], io_to_bank_wr_en[i])
            self.wire(self.io_ctrl.ports.io_to_bank_wr_data[i], io_to_bank_wr_data[i])
            self.wire(self.io_ctrl.ports.io_to_bank_wr_data_bit_sel[i], io_to_bank_wr_data_bit_sel[i])
            self.wire(self.io_ctrl.ports.io_to_bank_wr_addr[i], io_to_bank_wr_addr[i])
            self.wire(self.io_ctrl.ports.io_to_bank_rd_en[i], io_to_bank_rd_en[i])
            self.wire(self.io_ctrl.ports.bank_to_io_rd_data[i], bank_to_io_rd_data[i])
            self.wire(self.io_ctrl.ports.io_to_bank_rd_addr[i], io_to_bank_rd_addr[i])

        # cgra ports
        self.wire(self.ports.cgra_to_io_wr_en, self.io_ctrl.ports.cgra_to_io_wr_en)
        self.wire(self.ports.cgra_to_io_rd_en, self.io_ctrl.ports.cgra_to_io_rd_en)
        self.wire(self.ports.io_to_cgra_rd_data_valid, self.io_ctrl.ports.io_to_cgra_rd_data_valid)
        self.wire(self.ports.cgra_to_io_wr_data, self.io_ctrl.ports.cgra_to_io_wr_data)
        self.wire(self.ports.io_to_cgra_rd_data, self.io_ctrl.ports.io_to_cgra_rd_data)
        self.wire(self.ports.cgra_to_io_addr_high, self.io_ctrl.ports.cgra_to_io_addr_high)
        self.wire(self.ports.cgra_to_io_addr_low, self.io_ctrl.ports.cgra_to_io_addr_low)

        # io controller config
        glb_config_en_io=[m.Bit]*self.num_banks
        eq = FromMagma(mantle.DefineEQ(2))
        self.wire(Const(1), eq.ports.I0)
        self.wire(self.ports.glb_config_addr[10:12], eq.ports.I1)
        glb_config_en_io=eq.ports.O

        # io_controller configuration wiring
        self.wire(glb_config_en_io, self.io_ctrl.ports.config_en)
        self.wire(self.ports.glb_config_wr, self.io_ctrl.ports.config_wr)
        self.wire(self.ports.glb_config_rd, self.io_ctrl.ports.config_rd)
        self.wire(self.ports.glb_config_addr[2:10], self.io_ctrl.ports.config_addr)
        self.wire(self.ports.glb_config_wr_data, self.io_ctrl.ports.config_wr_data)
        config_rd_data_io=self.io_ctrl.ports.config_rd_data

        # cfg_controller
        self.cfg_ctrl = CfgController(self.num_banks, self.num_cfg_channels)
        self.wire(self.ports.clk, self.cfg_ctrl.ports.clk)
        self.wire(self.ports.reset, self.cfg_ctrl.ports.reset)
        self.wire(self.ports.config_start_pulse, self.cfg_ctrl.ports.config_start_pulse)
        self.wire(self.ports.config_done_pulse, self.cfg_ctrl.ports.config_done_pulse)

        # cfg_controller - bank wiring
        for i in range(self.num_banks):
            self.wire(self.cfg_ctrl.ports.cfg_to_bank_rd_en[i], cfg_to_bank_rd_en[i])
            self.wire(self.cfg_ctrl.ports.bank_to_cfg_rd_data[i], bank_to_cfg_rd_data[i])
            self.wire(self.cfg_ctrl.ports.cfg_to_bank_rd_addr[i], cfg_to_bank_rd_addr[i])

        # glc ports
        self.wire(self.ports.glc_to_cgra_cfg_wr, self.cfg_ctrl.ports.glc_to_cgra_cfg_wr)
        self.wire(self.ports.glc_to_cgra_cfg_rd, self.cfg_ctrl.ports.glc_to_cgra_cfg_rd)
        self.wire(self.ports.glc_to_cgra_cfg_addr, self.cfg_ctrl.ports.glc_to_cgra_cfg_addr)
        self.wire(self.ports.glc_to_cgra_cfg_data, self.cfg_ctrl.ports.glc_to_cgra_cfg_data)

        # parallel config output
        self.wire(self.ports.glb_to_cgra_cfg_wr, self.cfg_ctrl.ports.glb_to_cgra_cfg_wr)
        self.wire(self.ports.glb_to_cgra_cfg_rd, self.cfg_ctrl.ports.glb_to_cgra_cfg_rd)
        self.wire(self.ports.glb_to_cgra_cfg_addr, self.cfg_ctrl.ports.glb_to_cgra_cfg_addr)
        self.wire(self.ports.glb_to_cgra_cfg_data, self.cfg_ctrl.ports.glb_to_cgra_cfg_data)

        # cfg controller config
        glb_config_en_cfg=[m.Bit]*self.num_banks
        eq = FromMagma(mantle.DefineEQ(2))
        self.wire(Const(2), eq.ports.I0)
        self.wire(self.ports.glb_config_addr[10:12], eq.ports.I1)
        glb_config_en_cfg=eq.ports.O

        # cfg_controller configuration wiring
        self.wire(glb_config_en_cfg, self.cfg_ctrl.ports.config_en)
        self.wire(self.ports.glb_config_wr, self.cfg_ctrl.ports.config_wr)
        self.wire(self.ports.glb_config_rd, self.cfg_ctrl.ports.config_rd)
        self.wire(self.ports.glb_config_addr[2:10], self.cfg_ctrl.ports.config_addr)
        self.wire(self.ports.glb_config_wr_data, self.cfg_ctrl.ports.config_wr_data)
        config_rd_data_cfg=self.cfg_ctrl.ports.config_rd_data

        # configuration read
        and_ = FromMagma(mantle.DefineAnd(2, 1))
        self.wire(and_.ports.I0[0], self.ports.glb_config_rd)
        self.wire(and_.ports.I1[0], glb_config_en_io)
        and_1 = FromMagma(mantle.DefineAnd(2, 1))
        self.wire(and_1.ports.I0[0], self.ports.glb_config_rd)
        self.wire(and_1.ports.I1[0], glb_config_en_cfg)

        encoder = FromMagma(mantle.DefineEncoder(2))
        self.wire(encoder.ports.I[0], and_.ports.O[0])
        self.wire(encoder.ports.I[1], and_1.ports.O[0])

        config_rd_mux = MuxWithDefaultWrapper(2, 32, 2, 0)
        self.wire(self.ports.glb_config_rd, config_rd_mux.ports.EN[0])
        self.wire(encoder.ports.O[0], config_rd_mux.ports.S[0])
        self.wire(Const(0), config_rd_mux.ports.S[1])
        self.wire(config_rd_mux.ports.I[0], config_rd_data_io)
        self.wire(config_rd_mux.ports.I[1], config_rd_data_cfg)
        self.wire(self.ports.glb_config_rd_data, config_rd_mux.ports.O)

    def name(self):
        return f"GlobalBuffer_{self.num_banks}_{self.num_io_channels}_{self.num_cfg_channels}"

#global_buffer = GlobalBuffer(32, 8, 8)
#m.compile("global_buffer", global_buffer.circuit(), output="coreir-verilog")
