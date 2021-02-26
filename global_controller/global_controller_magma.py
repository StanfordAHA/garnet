import magma as m
from gemstone.common.jtag_type import JTAGType
from gemstone.common.configurable import ConfigurationType
from gemstone.generator.from_magma import FromMagma
from gemstone.generator.generator import Generator
from gemstone.generator.const import Const
from .global_controller_genesis2 import gen_wrapper, GlobalControllerParams
from cgra.ifc_struct import *


class GlobalController(m.Generator2):
    def __init__(self, addr_width=32, data_width=32,
                 axi_addr_width=12, axi_data_width=32,
                 num_glb_tiles=16, glb_addr_width=22,
                 block_axi_addr_width=12):
        
        self.addr_width = addr_width
        self.data_width = data_width
        self.axi_addr_width = axi_addr_width
        self.axi_data_width = axi_data_width
        self.num_glb_tiles = num_glb_tiles
        self.block_axi_addr_width = block_axi_addr_width
        
        self.name = f"GlobalController_cfg_{self.addr_width}_" \
                    f"{self.data_width}_axi_{self.axi_addr_width}_" \
                    f"{self.axi_data_width}"
        # Control logic assumes cgra config_data_width is same as axi_data_width
        assert self.axi_data_width == self.data_width

        self.glb_addr_width = glb_addr_width
        self.config_type = ConfigurationType(self.addr_width, self.data_width)

        self.io = m.IO(
            clk_in=m.In(m.Clock),
            reset_in=m.In(m.AsyncReset),

            clk_out=m.Out(m.Clock),
            reset_out=m.Out(m.AsyncReset),
            cgra_stall=m.Out(m.Bits[self.num_glb_tiles]),
            glb_stall=m.Out(m.Bits[self.num_glb_tiles]),
            soft_reset=m.Out(m.Bit),

            glb_cfg=GlbCfgIfc(self.block_axi_addr_width,
                              self.axi_data_width).master,
            sram_cfg=GlbCfgIfc(self.glb_addr_width, self.axi_data_width).master,

            strm_start_pulse=m.Out(m.Bits[self.num_glb_tiles]),
            pc_start_pulse=m.Out(m.Bits[self.num_glb_tiles]),
            strm_g2f_interrupt_pulse=m.In(m.Bits[self.num_glb_tiles]),
            strm_f2g_interrupt_pulse=m.In(m.Bits[self.num_glb_tiles]),
            pcfg_g2f_interrupt_pulse=m.In(m.Bits[self.num_glb_tiles]),

            cgra_config=m.Out(self.config_type),
            read_data_in=m.In(m.Bits[self.data_width]),
            jtag=JTAGType,
            axi4_slave=AXI4LiteIfc(self.axi_addr_width, self.data_width).slave,
            interrupt=m.Out(m.Bit)
        )

        params = GlobalControllerParams(cfg_data_width=self.data_width,
                                        cfg_addr_width=self.addr_width,
                                        axi_addr_width=self.axi_addr_width,
                                        axi_data_width=self.axi_data_width,
                                        num_glb_tiles=self.num_glb_tiles,
                                        block_axi_addr_width=(
                                            self.block_axi_addr_width))

        wrapper = gen_wrapper(params)
        generator = wrapper.generator(mode="declare")
        self.underlying = FromMagma(generator())

        # wire clk and reset
        m.wire(self.io.clk_in, self.underlying.clk_in)
        m.wire(self.io.reset_in, self.underlying.reset_in)

        # cgra control signals
        m.wire(self.underlying.clk_out, self.io.clk_out)
        m.wire(self.underlying.reset_out, self.io.reset_out)
        m.wire(self.underlying.cgra_stall, self.io.cgra_stall)
        m.wire(self.underlying.glb_stall, self.io.glb_stall)
        m.wire(self.underlying.soft_reset, self.io.soft_reset)

        # global buffer configuration
        m.wire(self.io.glb_cfg.wr_en, self.underlying.glb_cfg_wr_en)
        m.wire(self.io.glb_cfg.wr_clk_en, self.underlying.glb_cfg_wr_clk_en)
        m.wire(self.io.glb_cfg.wr_addr, self.underlying.glb_cfg_wr_addr)
        m.wire(self.io.glb_cfg.wr_data, self.underlying.glb_cfg_wr_data)
        m.wire(self.io.glb_cfg.rd_en, self.underlying.glb_cfg_rd_en)
        m.wire(self.io.glb_cfg.rd_clk_en, self.underlying.glb_cfg_rd_clk_en)
        m.wire(self.io.glb_cfg.rd_addr, self.underlying.glb_cfg_rd_addr)
        m.wire(self.underlying.glb_cfg_rd_data, self.io.glb_cfg.rd_data)
        m.wire(self.underlying.glb_cfg_rd_data_valid,
               self.io.glb_cfg.rd_data_valid)

        # global buffer sram configuration
        m.wire(self.io.sram_cfg.wr_en, self.underlying.sram_cfg_wr_en)
        m.wire(self.io.sram_cfg.wr_clk_en, self.underlying.sram_cfg_wr_clk_en)
        m.wire(self.io.sram_cfg.wr_addr, self.underlying.sram_cfg_wr_addr)
        m.wire(self.io.sram_cfg.wr_data, self.underlying.sram_cfg_wr_data)
        m.wire(self.io.sram_cfg.rd_en, self.underlying.sram_cfg_rd_en)
        m.wire(self.io.sram_cfg.rd_clk_en, self.underlying.sram_cfg_rd_clk_en)
        m.wire(self.io.sram_cfg.rd_addr, self.underlying.sram_cfg_rd_addr)
        m.wire(self.underlying.sram_cfg_rd_data, self.io.sram_cfg.rd_data)
        m.wire(self.underlying.sram_cfg_rd_data_valid,
               self.io.sram_cfg.rd_data_valid)

        # start/done pulse
        m.wire(self.underlying.strm_f2g_interrupt_pulse,
               self.io.strm_f2g_interrupt_pulse)
        m.wire(self.underlying.strm_g2f_interrupt_pulse,
               self.io.strm_g2f_interrupt_pulse)
        m.wire(self.underlying.pcfg_g2f_interrupt_pulse,
               self.io.pcfg_g2f_interrupt_pulse)
        m.wire(self.io.strm_start_pulse,
               self.underlying.strm_start_pulse)
        m.wire(self.io.pc_start_pulse,
               self.underlying.pc_start_pulse)

        # cgra configuration interface
        m.wire(self.underlying.cgra_cfg_addr,
               self.io.cgra_config.config_addr)
        m.wire(self.underlying.cgra_cfg_wr_data,
               self.io.cgra_config.config_data)
        m.wire(self.underlying.cgra_cfg_read,
               self.io.cgra_config.read[0])
        m.wire(self.underlying.cgra_cfg_write,
               self.io.cgra_config.write[0])
        m.wire(self.io.read_data_in,
               self.underlying.cgra_cfg_rd_data)

        # axi4-lite slave interface
        m.wire(self.io.axi4_slave.awaddr,
               self.underlying.axi_awaddr)
        m.wire(self.io.axi4_slave.awvalid,
               self.underlying.axi_awvalid)
        m.wire(self.io.axi4_slave.awready,
               self.underlying.axi_awready)
        m.wire(self.io.axi4_slave.wdata,
               self.underlying.axi_wdata)
        m.wire(self.io.axi4_slave.wvalid,
               self.underlying.axi_wvalid)
        m.wire(self.io.axi4_slave.wready,
               self.underlying.axi_wready)
        m.wire(self.io.axi4_slave.bready,
               self.underlying.axi_bready)
        m.wire(self.io.axi4_slave.bvalid,
               self.underlying.axi_bvalid)
        m.wire(self.io.axi4_slave.bresp,
               self.underlying.axi_bresp)
        m.wire(self.io.axi4_slave.araddr,
               self.underlying.axi_araddr)
        m.wire(self.io.axi4_slave.arvalid,
               self.underlying.axi_arvalid)
        m.wire(self.io.axi4_slave.arready,
               self.underlying.axi_arready)
        m.wire(self.io.axi4_slave.rdata,
               self.underlying.axi_rdata)
        m.wire(self.io.axi4_slave.rresp,
               self.underlying.axi_rresp)
        m.wire(self.io.axi4_slave.rvalid,
               self.underlying.axi_rvalid)
        m.wire(self.io.axi4_slave.rready,
               self.underlying.axi_rready)

        # interrupt
        m.wire(self.io.interrupt, self.underlying.interrupt)

        # jtag interface signals
        m.wire(self.io.jtag.tdi, self.underlying.tdi)
        m.wire(self.io.jtag.tdo, self.underlying.tdo)
        m.wire(self.io.jtag.tms, self.underlying.tms)
        m.wire(self.io.jtag.tck, self.underlying.tck)
        m.wire(self.io.jtag.trst_n, self.underlying.trst_n)

