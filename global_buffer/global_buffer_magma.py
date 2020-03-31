import magma
from gemstone.generator.from_magma import FromMagma
from gemstone.generator.generator import Generator
from global_buffer.ifc_struct import *
from global_buffer.global_buffer_magma_helper import *

class GlobalBuffer(Generator):
    def __init__(self, num_glb_tiles, num_cgra_cols, banks_per_tile=2,
                 bank_addr_width=17, bank_data_width=64, cgra_data_width=16,
                 axi_addr_width=12, axi_data_width=32,
                 cfg_addr_width=32, cfg_data_width=32):

        super().__init__()

        self.num_glb_tiles = num_glb_tiles
        self.num_cgra_cols = num_cgra_cols
        self.col_per_glb = num_cgra_cols // num_glb_tiles
        self.banks_per_tile = banks_per_tile
        self.bank_addr_width = bank_addr_width
        self.bank_data_width = bank_data_width
        self.cgra_data_width = cgra_data_width
        self.axi_addr_width = axi_addr_width
        self.axi_data_width = axi_data_width
        self.cfg_addr_width = cfg_addr_width
        self.cfg_data_width = cfg_data_width
        self.glb_addr_width = (self.bank_addr_width
                               + magma.bitutils.clog2(self.col_per_glb)
                               + magma.bitutils.clog2(self.num_glb_tiles))

        self.cgra_jtag_cfg_type = CgraCfgStruct(self.cfg_addr_width,
                                                self.cfg_data_width)
        self.cgra_pc_cfg_type = CgraCfgStruct(self.cfg_addr_width,
                                              self.cfg_data_width,
                                              self.num_cgra_cols)


        self.add_ports(
            clk=magma.In(magma.Clock),
            reset=magma.In(magma.AsyncReset),
            stall=magma.In(magma.Bit),

            proc_packet=ProcPacketIfc(self.glb_addr_width,
                                      self.bank_data_width),
            glb_cfg=GlbCfgIfc(self.axi_addr_width, self.axi_data_width),
            sram_cfg=GlbCfgIfc(self.glb_addr_width, self.axi_data_width),

            stream_data_f2g=magma.In(magma.Bits[(self.num_cgra_cols
                                                 *self.cgra_data_width)]),
            stream_data_valid_f2g=magma.In(magma.Bits[self.num_cgra_cols]),
            stream_data_g2f=magma.Out(magma.Bits[(self.num_cgra_cols
                                                  *self.cgra_data_width)]),
            stream_data_valid_g2f=magma.Out(magma.Bits[self.num_cgra_cols]),

            cgra_cfg_jtag=magma.In(self.cgra_jtag_cfg_type),
            cgra_cfg_g2f=magma.Out(self.cgra_pc_cfg_type),

            strm_start_pulse=magma.In(magma.Bits[self.num_glb_tiles]),
            pc_start_pulse=magma.In(magma.Bits[self.num_glb_tiles]),
            interrupt_pulse=magma.Out(magma.Bits[3*self.num_glb_tiles]),
        )

        # parameter
        # TODO(kongty)
        params = GlobalBufferParams()
        self.underlying = FromMagma(GlobalBufferDeclarationGenerator(params))

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

        self.wire(self.ports.stream_data_f2g,
                  self.underlying.ports.stream_data_f2g)
        self.wire(self.ports.stream_data_valid_f2g,
                  self.underlying.ports.stream_data_valid_f2g)
        self.wire(self.ports.stream_data_g2f,
                  self.underlying.ports.stream_data_g2f)
        self.wire(self.ports.stream_data_valid_g2f,
                  self.underlying.ports.stream_data_valid_g2f)

        self.wire(self.ports.cgra_cfg_jtag.wr_en,
                  self.underlying.ports.cgra_cfg_jtag_gc2glb_wr_en)
        self.wire(self.ports.cgra_cfg_jtag.rd_en,
                  self.underlying.ports.cgra_cfg_jtag_gc2glb_rd_en)
        self.wire(self.ports.cgra_cfg_jtag.addr,
                  self.underlying.ports.cgra_cfg_jtag_gc2glb_addr)
        self.wire(self.ports.cgra_cfg_jtag.data,
                  self.underlying.ports.cgra_cfg_jtag_gc2glb_data)

        self.wire(self.ports.cgra_cfg_g2f.wr_en,
                  self.underlying.ports.cgra_cfg_g2f_cfg_wr_en)
        self.wire(self.ports.cgra_cfg_g2f.rd_en,
                  self.underlying.ports.cgra_cfg_g2f_cfg_rd_en)
        self.wire(self.ports.cgra_cfg_g2f.addr,
                  self.underlying.ports.cgra_cfg_g2f_cfg_addr)
        self.wire(self.ports.cgra_cfg_g2f.data,
                  self.underlying.ports.cgra_cfg_g2f_cfg_data)

        self.wire(self.ports.strm_start_pulse,
                  self.underlying.ports.strm_start_pulse)
        self.wire(self.ports.pc_start_pulse,
                  self.underlying.ports.pc_start_pulse)
        self.wire(self.ports.interrupt_pulse,
                  self.underlying.ports.interrupt_pulse)

    def name(self):
        return f"GlobalBuffer_{self.num_glb_tiles}_{self.num_cgra_cols}"

def main():
    global_buffer = GlobalBuffer(16, 32)
    global_buffer_circ = global_buffer.circuit()
    magma.compile("global_buffer", global_buffer_circ, output="verilog")

if __name__ == "__main__":
    main()
