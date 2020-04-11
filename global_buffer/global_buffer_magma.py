import magma
from gemstone.generator.from_magma import FromMagma
from gemstone.common.configurable import ConfigurationType
from gemstone.generator.generator import Generator
from cgra.ifc_struct import ProcPacketIfc, GlbCfgIfc
from global_buffer.global_buffer_magma_helper import *


class GlobalBuffer(Generator):
    def __init__(self, num_glb_tiles, num_cgra_cols, banks_per_tile=2,
                 bank_addr_width=17, bank_data_width=64, cgra_data_width=16,
                 axi_addr_width=12, axi_data_width=32,
                 cfg_addr_width=32, cfg_data_width=32):

        super().__init__()

        self.num_glb_tiles = num_glb_tiles
        self.num_cgra_cols = num_cgra_cols

        # the number of glb tiles is half the number of cgra columns
        assert 2 * self.num_glb_tiles == self.num_cgra_cols

        self.col_per_tile = num_cgra_cols // num_glb_tiles
        self.banks_per_tile = banks_per_tile
        self.bank_addr_width = bank_addr_width
        self.bank_data_width = bank_data_width
        self.cgra_data_width = cgra_data_width
        self.axi_addr_width = axi_addr_width
        self.axi_data_width = axi_data_width
        self.cfg_addr_width = cfg_addr_width
        self.cfg_data_width = cfg_data_width
        self.glb_addr_width = (self.bank_addr_width
                               + magma.bitutils.clog2(self.banks_per_tile)
                               + magma.bitutils.clog2(self.num_glb_tiles))
        self.tile_sel_addr_width = m.bitutils.clog2(self.num_glb_tiles)
        self.cgra_per_glb = self.num_cgra_cols // self.num_glb_tiles
        self.bank_sel_addr_width = m.bitutils.clog2(self.banks_per_tile)

        self.cgra_cfg_type = ConfigurationType(self.cfg_addr_width,
                                               self.cfg_data_width)

        self.add_ports(
            clk=magma.In(magma.Clock),
            reset=magma.In(magma.AsyncReset),
            stall=magma.In(magma.Bit),

            proc_packet=ProcPacketIfc(self.glb_addr_width,
                                      self.bank_data_width).slave,
            glb_cfg=GlbCfgIfc(self.axi_addr_width, self.axi_data_width).slave,
            sram_cfg=GlbCfgIfc(self.glb_addr_width, self.axi_data_width).slave,

            stream_data_f2g=magma.In(magma.Array[self.num_cgra_cols,
                                                 magma.Bits
                                                 [self.cgra_data_width]]),
            stream_data_valid_f2g=magma.In(magma.Array[self.num_cgra_cols,
                                                       magma.Bits[1]]),
            stream_data_g2f=magma.Out(magma.Array[self.num_cgra_cols,
                                                  magma.Bits
                                                  [self.cgra_data_width]]),
            stream_data_valid_g2f=magma.Out(magma.Array[self.num_cgra_cols,
                                                        magma.Bits[1]]),

            cgra_cfg_jtag=magma.In(self.cgra_cfg_type),
            cgra_cfg_g2f=magma.Out(magma.Array[self.num_cgra_cols,
                                               self.cgra_cfg_type]),

            strm_start_pulse=magma.In(magma.Array[self.num_glb_tiles,
                                                  magma.Bits[1]]),
            pc_start_pulse=magma.In(magma.Array[self.num_glb_tiles,
                                                magma.Bits[1]]),
            interrupt_pulse=magma.Out(magma.Array[self.num_glb_tiles,
                                                  magma.Bits[3]]),
        )

        # parameter
        params = GlobalBufferParams(NUM_GLB_TILES=self.num_glb_tiles,
                                    TILE_SEL_ADDR_WIDTH=(
                                        self.tile_sel_addr_width),
                                    NUM_CGRA_TILES=self.num_cgra_cols,
                                    CGRA_PER_GLB=self.cgra_per_glb,
                                    BANKS_PER_TILE=self.banks_per_tile,
                                    BANK_SEL_ADDR_WIDTH=(
                                        self.bank_sel_addr_width),
                                    BANK_DATA_WIDTH=self.bank_data_width,
                                    BANK_ADDR_WIDTH=self.bank_addr_width,
                                    GLB_ADDR_WIDTH=self.glb_addr_width,
                                    CGRA_DATA_WIDTH=self.cgra_data_width,
                                    AXI_ADDR_WIDTH=self.axi_addr_width,
                                    AXI_DATA_WIDTH=self.axi_data_width,
                                    CGRA_CFG_ADDR_WIDTH=self.cfg_addr_width,
                                    CGRA_CFG_DATA_WIDTH=self.cfg_data_width)

        self.underlying = FromMagma(GlobalBufferSVWrapperGenerator(params))

        # wiring
        self.wire(self.ports.clk, self.underlying.ports.clk)
        self.wire(self.ports.stall, self.underlying.ports.stall)
        self.wire(self.ports.reset, self.underlying.ports.reset)

        self.wire(self.ports.proc_packet.wr_en,
                  self.underlying.ports.proc2glb_wr_en)
        self.wire(self.ports.proc_packet.wr_strb,
                  self.underlying.ports.proc2glb_wr_strb)
        self.wire(self.ports.proc_packet.wr_addr,
                  self.underlying.ports.proc2glb_wr_addr)
        self.wire(self.ports.proc_packet.wr_data,
                  self.underlying.ports.proc2glb_wr_data)
        self.wire(self.ports.proc_packet.rd_en,
                  self.underlying.ports.proc2glb_rd_en)
        self.wire(self.ports.proc_packet.rd_addr,
                  self.underlying.ports.proc2glb_rd_addr)
        self.wire(self.ports.proc_packet.rd_data,
                  self.underlying.ports.glb2proc_rd_data)
        self.wire(self.ports.proc_packet.rd_data_valid,
                  self.underlying.ports.glb2proc_rd_data_valid)

        self.wire(self.ports.glb_cfg.wr_en,
                  self.underlying.ports.glb_cfg_wr_en)
        self.wire(self.ports.glb_cfg.wr_clk_en,
                  self.underlying.ports.glb_cfg_wr_clk_en)
        self.wire(self.ports.glb_cfg.wr_addr,
                  self.underlying.ports.glb_cfg_wr_addr)
        self.wire(self.ports.glb_cfg.wr_data,
                  self.underlying.ports.glb_cfg_wr_data)
        self.wire(self.ports.glb_cfg.rd_en,
                  self.underlying.ports.glb_cfg_rd_en)
        self.wire(self.ports.glb_cfg.rd_clk_en,
                  self.underlying.ports.glb_cfg_rd_clk_en)
        self.wire(self.ports.glb_cfg.rd_addr,
                  self.underlying.ports.glb_cfg_rd_addr)
        self.wire(self.ports.glb_cfg.rd_data,
                  self.underlying.ports.glb_cfg_rd_data)
        self.wire(self.ports.glb_cfg.rd_data_valid,
                  self.underlying.ports.glb_cfg_rd_data_valid)

        self.wire(self.ports.sram_cfg.wr_en,
                  self.underlying.ports.sram_cfg_wr_en)
        self.wire(self.ports.sram_cfg.wr_clk_en,
                  self.underlying.ports.sram_cfg_wr_clk_en)
        self.wire(self.ports.sram_cfg.wr_addr,
                  self.underlying.ports.sram_cfg_wr_addr)
        self.wire(self.ports.sram_cfg.wr_data,
                  self.underlying.ports.sram_cfg_wr_data)
        self.wire(self.ports.sram_cfg.rd_en,
                  self.underlying.ports.sram_cfg_rd_en)
        self.wire(self.ports.sram_cfg.rd_clk_en,
                  self.underlying.ports.sram_cfg_rd_clk_en)
        self.wire(self.ports.sram_cfg.rd_addr,
                  self.underlying.ports.sram_cfg_rd_addr)
        self.wire(self.ports.sram_cfg.rd_data,
                  self.underlying.ports.sram_cfg_rd_data)
        self.wire(self.ports.sram_cfg.rd_data_valid,
                  self.underlying.ports.sram_cfg_rd_data_valid)

        for i in range(self.num_cgra_cols):
            self.wire(self.ports.stream_data_f2g[i],
                      self.underlying.ports.stream_data_f2g
                      [i * self.cgra_data_width:(i + 1) * self.cgra_data_width])
            self.wire(self.ports.stream_data_valid_f2g[i][0],
                      self.underlying.ports.stream_data_valid_f2g[i])
            self.wire(self.ports.stream_data_g2f[i],
                      self.underlying.ports.stream_data_g2f
                      [i * self.cgra_data_width:(i + 1) * self.cgra_data_width])
            self.wire(self.ports.stream_data_valid_g2f[i][0],
                      self.underlying.ports.stream_data_valid_g2f[i])

        self.wire(self.ports.cgra_cfg_jtag.write,
                  self.underlying.ports.cgra_cfg_jtag_gc2glb_wr_en)
        self.wire(self.ports.cgra_cfg_jtag.read,
                  self.underlying.ports.cgra_cfg_jtag_gc2glb_rd_en)
        self.wire(self.ports.cgra_cfg_jtag.config_addr,
                  self.underlying.ports.cgra_cfg_jtag_gc2glb_addr)
        self.wire(self.ports.cgra_cfg_jtag.config_data,
                  self.underlying.ports.cgra_cfg_jtag_gc2glb_data)

        for i in range(self.num_cgra_cols):
            self.wire(self.ports.cgra_cfg_g2f[i].write[0],
                      self.underlying.ports.cgra_cfg_g2f_cfg_wr_en[i])
            self.wire(self.ports.cgra_cfg_g2f[i].read[0],
                      self.underlying.ports.cgra_cfg_g2f_cfg_rd_en[i])
            self.wire(self.ports.cgra_cfg_g2f[i].config_addr,
                      self.underlying.ports.cgra_cfg_g2f_cfg_addr
                      [i * self.cfg_addr_width:(i + 1) * self.cfg_addr_width])
            self.wire(self.ports.cgra_cfg_g2f[i].config_data,
                      self.underlying.ports.cgra_cfg_g2f_cfg_data
                      [i * self.cfg_data_width:(i + 1) * self.cfg_data_width])

        for i in range(self.num_glb_tiles):
            self.wire(self.ports.strm_start_pulse[i][0],
                      self.underlying.ports.strm_start_pulse[i])
            self.wire(self.ports.pc_start_pulse[i][0],
                      self.underlying.ports.pc_start_pulse[i])
            self.wire(self.ports.interrupt_pulse[i],
                      self.underlying.ports.interrupt_pulse[i * 3:(i + 1) * 3])

    def name(self):
        return f"GlobalBuffer_{self.num_glb_tiles}_{self.num_cgra_cols}"
