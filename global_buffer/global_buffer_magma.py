import magma as m
from gemstone.generator.from_magma import FromMagma
from gemstone.common.configurable import ConfigurationType
from gemstone.generator.generator import Generator
from cgra.ifc_struct import ProcPacketIfc, GlbCfgIfc
from .global_buffer_magma_helper import *


class GlobalBuffer(m.Generator2):
    def __init__(self, num_glb_tiles, num_cgra_cols, banks_per_tile=2,
                 bank_addr_width=17, bank_data_width=64, cgra_data_width=16,
                 axi_addr_width=12, axi_data_width=32,
                 cfg_addr_width=32, cfg_data_width=32,
                 parameter_only: bool = False):

        self.name = f"GlobalBuffer_{self.num_glb_tiles}_{self.num_cgra_cols}"

        self.num_glb_tiles = num_glb_tiles
        self.num_cgra_cols = num_cgra_cols

        # the number of glb tiles is half the number of cgra columns
        assert 2 * self.num_glb_tiles == self.num_cgra_cols

        self.col_per_tile = num_cgra_cols // num_glb_tiles
        self.banks_per_tile = banks_per_tile
        self.bank_addr_width = bank_addr_width
        self.bank_data_width = bank_data_width
        self.bank_byte_offset = m.bitutils.clog2(self.bank_data_width // 8)
        self.cgra_data_width = cgra_data_width
        self.cgra_byte_offset = m.bitutils.clog2(self.cgra_data_width // 8)
        self.axi_addr_width = axi_addr_width
        self.axi_data_width = axi_data_width
        self.axi_strb_width = self.axi_data_width // 8
        self.axi_byte_offset = m.bitutils.clog2(self.axi_data_width // 8)
        self.cfg_addr_width = cfg_addr_width
        self.cfg_data_width = cfg_data_width
        self.glb_addr_width = (self.bank_addr_width
                               + m.bitutils.clog2(self.banks_per_tile)
                               + m.bitutils.clog2(self.num_glb_tiles))
        self.tile_sel_addr_width = m.bitutils.clog2(self.num_glb_tiles)
        self.cgra_per_glb = self.num_cgra_cols // self.num_glb_tiles
        self.bank_sel_addr_width = m.bitutils.clog2(self.banks_per_tile)

        self.cgra_cfg_type = ConfigurationType(self.cfg_addr_width,
                                               self.cfg_data_width)
        self.max_num_words_width = (self.glb_addr_width - self.bank_byte_offset
                                    + m.bitutils.clog2(bank_data_width
                                                           // cgra_data_width))
        self.max_stride_width = 10
        self.max_num_cfgs_width = self.glb_addr_width - self.bank_byte_offset
        self.queue_depth = 4
        self.loop_level = 4
        self.latency_width = 2 + m.bitutils.clog2(self.num_glb_tiles)

        self.io = m.IO(
            clk=m.In(m.Clock),
            reset=m.In(m.AsyncReset),
            stall=m.In(m.Bits[self.num_glb_tiles]),
            cgra_stall_in=m.In(m.Bits[self.num_glb_tiles]),
            cgra_soft_reset=m.In(m.Bit),

            proc_packet=ProcPacketIfc(self.glb_addr_width,
                                      self.bank_data_width).slave,
            glb_cfg=GlbCfgIfc(self.axi_addr_width, self.axi_data_width).slave,
            sram_cfg=GlbCfgIfc(self.glb_addr_width, self.axi_data_width).slave,

            stream_data_f2g=m.In(m.Array[self.num_cgra_cols,
                                                 m.Bits
                                                 [self.cgra_data_width]]),
            stream_data_valid_f2g=m.In(m.Array[self.num_cgra_cols,
                                                       m.Bits[1]]),
            stream_data_g2f=m.Out(m.Array[self.num_cgra_cols,
                                                  m.Bits
                                                  [self.cgra_data_width]]),
            stream_data_valid_g2f=m.Out(m.Array[self.num_cgra_cols,
                                                        m.Bits[1]]),

            cgra_cfg_jtag=m.In(self.cgra_cfg_type),
            cgra_cfg_g2f=m.Out(m.Array[self.num_cgra_cols,
                                               self.cgra_cfg_type]),

            cgra_stall=m.Out(m.Bits[self.num_cgra_cols]),

            strm_start_pulse=m.In(m.Bits[self.num_glb_tiles]),
            pc_start_pulse=m.In(m.Bits[self.num_glb_tiles]),
            strm_f2g_interrupt_pulse=m.Out(m.Bits[self.num_glb_tiles]),
            strm_g2f_interrupt_pulse=m.Out(m.Bits[self.num_glb_tiles]),
            pcfg_g2f_interrupt_pulse=m.Out(m.Bits[self.num_glb_tiles])
        )

        # parameter
        self.param = GlobalBufferParams(NUM_GLB_TILES=self.num_glb_tiles,
                                        TILE_SEL_ADDR_WIDTH=(
                                            self.tile_sel_addr_width),
                                        NUM_CGRA_TILES=self.num_cgra_cols,
                                        CGRA_PER_GLB=self.cgra_per_glb,
                                        BANKS_PER_TILE=self.banks_per_tile,
                                        BANK_SEL_ADDR_WIDTH=(
                                            self.bank_sel_addr_width),
                                        BANK_DATA_WIDTH=self.bank_data_width,
                                        BANK_ADDR_WIDTH=self.bank_addr_width,
                                        BANK_BYTE_OFFSET=self.bank_byte_offset,
                                        GLB_ADDR_WIDTH=self.glb_addr_width,
                                        CGRA_DATA_WIDTH=self.cgra_data_width,
                                        CGRA_BYTE_OFFSET=self.cgra_byte_offset,
                                        AXI_ADDR_WIDTH=self.axi_addr_width,
                                        AXI_DATA_WIDTH=self.axi_data_width,
                                        AXI_STRB_WIDTH=self.axi_strb_width,
                                        AXI_BYTE_OFFSET=self.axi_byte_offset,
                                        MAX_NUM_WORDS_WIDTH=(
                                            self.max_num_words_width),
                                        MAX_STRIDE_WIDTH=(
                                            self.max_stride_width),
                                        MAX_NUM_CFGS_WIDTH=(
                                            self.max_num_cfgs_width),
                                        CGRA_CFG_ADDR_WIDTH=self.cfg_addr_width,
                                        CGRA_CFG_DATA_WIDTH=self.cfg_data_width,
                                        QUEUE_DEPTH=self.queue_depth,
                                        LOOP_LEVEL=self.loop_level,
                                        LATENCY_WIDTH=self.latency_width)

        # instantiate global buffer declaration
        self.glb_dcl = GlobalBufferDeclarationGenerator(self.param)

        self.glb_dcl.gen_param_files()
        if parameter_only:
            return

        self.underlying = FromMagma(self.glb_dcl)

        # wiring
        m.wire(self.io.clk, self.underlying.clk)
        m.wire(self.io.stall, self.underlying.stall)
        m.wire(self.io.cgra_stall_in, self.underlying.cgra_stall_in)
        m.wire(self.io.reset, self.underlying.reset)
        m.wire(self.io.cgra_soft_reset,
                  self.underlying.cgra_soft_reset)

        m.wire(self.io.proc_packet.wr_en,
                  self.underlying.proc_wr_en)
        m.wire(self.io.proc_packet.wr_strb,
                  self.underlying.proc_wr_strb)
        m.wire(self.io.proc_packet.wr_addr,
                  self.underlying.proc_wr_addr)
        m.wire(self.io.proc_packet.wr_data,
                  self.underlying.proc_wr_data)
        m.wire(self.io.proc_packet.rd_en,
                  self.underlying.proc_rd_en)
        m.wire(self.io.proc_packet.rd_addr,
                  self.underlying.proc_rd_addr)
        m.wire(self.io.proc_packet.rd_data,
                  self.underlying.proc_rd_data)
        m.wire(self.io.proc_packet.rd_data_valid,
                  self.underlying.proc_rd_data_valid)

        m.wire(self.io.glb_cfg.wr_en,
                  self.underlying.if_cfg_wr_en)
        m.wire(self.io.glb_cfg.wr_clk_en,
                  self.underlying.if_cfg_wr_clk_en)
        m.wire(self.io.glb_cfg.wr_addr,
                  self.underlying.if_cfg_wr_addr)
        m.wire(self.io.glb_cfg.wr_data,
                  self.underlying.if_cfg_wr_data)
        m.wire(self.io.glb_cfg.rd_en,
                  self.underlying.if_cfg_rd_en)
        m.wire(self.io.glb_cfg.rd_clk_en,
                  self.underlying.if_cfg_rd_clk_en)
        m.wire(self.io.glb_cfg.rd_addr,
                  self.underlying.if_cfg_rd_addr)
        m.wire(self.io.glb_cfg.rd_data,
                  self.underlying.if_cfg_rd_data)
        m.wire(self.io.glb_cfg.rd_data_valid,
                  self.underlying.if_cfg_rd_data_valid)

        m.wire(self.io.sram_cfg.wr_en,
                  self.underlying.if_sram_cfg_wr_en)
        m.wire(self.io.sram_cfg.wr_clk_en,
                  self.underlying.if_sram_cfg_wr_clk_en)
        m.wire(self.io.sram_cfg.wr_addr,
                  self.underlying.if_sram_cfg_wr_addr)
        m.wire(self.io.sram_cfg.wr_data,
                  self.underlying.if_sram_cfg_wr_data)
        m.wire(self.io.sram_cfg.rd_en,
                  self.underlying.if_sram_cfg_rd_en)
        m.wire(self.io.sram_cfg.rd_clk_en,
                  self.underlying.if_sram_cfg_rd_clk_en)
        m.wire(self.io.sram_cfg.rd_addr,
                  self.underlying.if_sram_cfg_rd_addr)
        m.wire(self.io.sram_cfg.rd_data,
                  self.underlying.if_sram_cfg_rd_data)
        m.wire(self.io.sram_cfg.rd_data_valid,
                  self.underlying.if_sram_cfg_rd_data_valid)

        for i in range(self.num_cgra_cols):
            m.wire(self.io.stream_data_f2g[i],
                      self.underlying.stream_data_f2g
                      [i * self.cgra_data_width:(i + 1) * self.cgra_data_width])
            m.wire(self.io.stream_data_valid_f2g[i][0],
                      self.underlying.stream_data_valid_f2g[i])
            m.wire(self.io.stream_data_g2f[i],
                      self.underlying.stream_data_g2f
                      [i * self.cgra_data_width:(i + 1) * self.cgra_data_width])
            m.wire(self.io.stream_data_valid_g2f[i][0],
                      self.underlying.stream_data_valid_g2f[i])

        m.wire(self.io.cgra_stall,
                  self.underlying.cgra_stall)

        m.wire(self.io.cgra_cfg_jtag.write,
                  self.underlying.cgra_cfg_jtag_gc2glb_wr_en)
        m.wire(self.io.cgra_cfg_jtag.read,
                  self.underlying.cgra_cfg_jtag_gc2glb_rd_en)
        m.wire(self.io.cgra_cfg_jtag.config_addr,
                  self.underlying.cgra_cfg_jtag_gc2glb_addr)
        m.wire(self.io.cgra_cfg_jtag.config_data,
                  self.underlying.cgra_cfg_jtag_gc2glb_data)

        for i in range(self.num_cgra_cols):
            m.wire(self.io.cgra_cfg_g2f[i].write[0],
                      self.underlying.cgra_cfg_g2f_cfg_wr_en[i])
            m.wire(self.io.cgra_cfg_g2f[i].read[0],
                      self.underlying.cgra_cfg_g2f_cfg_rd_en[i])
            m.wire(self.io.cgra_cfg_g2f[i].config_addr,
                      self.underlying.cgra_cfg_g2f_cfg_addr
                      [i * self.cfg_addr_width:(i + 1) * self.cfg_addr_width])
            m.wire(self.io.cgra_cfg_g2f[i].config_data,
                      self.underlying.cgra_cfg_g2f_cfg_data
                      [i * self.cfg_data_width:(i + 1) * self.cfg_data_width])

        m.wire(self.io.strm_start_pulse,
                  self.underlying.strm_start_pulse)
        m.wire(self.io.pc_start_pulse,
                  self.underlying.pc_start_pulse)
        m.wire(self.io.strm_f2g_interrupt_pulse,
                  self.underlying.strm_f2g_interrupt_pulse)
        m.wire(self.io.strm_g2f_interrupt_pulse,
                  self.underlying.strm_g2f_interrupt_pulse)
        m.wire(self.io.pcfg_g2f_interrupt_pulse,
                  self.underlying.pcfg_g2f_interrupt_pulse)

