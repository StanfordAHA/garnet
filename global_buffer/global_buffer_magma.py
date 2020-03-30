import magma
from math import log2, ceil
from gemstone.generator.from_verilog import FromVerilog
from gemstone.generator.generator import Generator
from global_buffer.ifc_struct import *

class GlobalBuffer(Generator):
    def __init__(self, num_glb_tiles, num_cgra_col, banks_per_tile=2,
                 bank_addr_width=17, bank_data_width=64, cgra_data_width=16,
                 axi_addr_width=12, axi_data_width=32,
                 cfg_addr_width=32, cfg_data_width=32):

        super().__init__()

        self.num_glb_tiles = num_glb_tiles
        self.num_cgra_col = num_cgra_col
        self.col_per_glb = num_cgra_col / num_glb_tiles
        self.banks_per_tile = banks_per_tile
        self.bank_addr_width = bank_addr_width
        self.bank_data_width = bank_data_width
        self.cgra_data_width = cgra_data_width
        self.axi_addr_width = axi_addr_width
        self.axi_data_width = axi_data_width
        self.cfg_addr_width = cfg_addr_width
        self.cfg_data_width = cfg_data_width
        self.glb_addr_width = (self.bank_addr_width
                               + ceil(log2(self.col_per_glb))
                               + ceil(log2(self.num_glb_tiles)))

        self.cgra_cfg_type = CgraCfgStruct(self.cfg_addr_width,
                                           self.cfg_data_width)

        self.add_ports(
            clk=magma.In(magma.Clock),
            reset=magma.In(magma.AsyncReset),
            stall=magma.In(magma.Bits[1]),

            proc_packet=ProcPacketIfc(self.glb_addr_width,
                                      self.bank_data_width),
            glb_cfg=GlbCfgIfc(self.axi_addr_width,
                              self.axi_data_width),
            sram_cfg=GlbCfgIfc(self.glb_addr_width,
                               self.axi_data_width),

            stream_data_f2g=magma.In(
                magma.Array[int(self.num_glb_tiles*self.col_per_glb),
                            magma.Bits[self.cgra_data_width]]),
            stream_data_valid_f2g=magma.In(
                magma.Array[int(self.num_glb_tiles*self.col_per_glb),
                            magma.Bits[1]]),
            stream_data_g2f=magma.Out(
                magma.Array[int(self.num_glb_tiles*self.col_per_glb),
                            magma.Bits[self.cgra_data_width]]),
            stream_data_valid_g2f=magma.Out(
                magma.Array[int(self.num_glb_tiles*self.col_per_glb),
                            magma.Bits[1]]),

            cgra_cfg_jtag=magma.In(self.cgra_cfg_type),
            cgra_cfg_g2f=magma.Out(
                magma.Array[int(self.num_glb_tiles*self.col_per_glb),
                            self.cgra_cfg_type]),

            strm_start_pulse=magma.In(magma.Bits[self.num_glb_tiles]),
            pc_start_pulse=magma.In(magma.Bits[self.num_glb_tiles]),
            interrupt_pulse=magma.Out(magma.Bits[3*self.num_glb_tiles]),
        )

        self.underlying = FromVerilog(filename="./global_buffer/rtl/global_buffer.sv")

    def name(self):
        return f"GlobalBuffer_{self.num_glb_tiles}_{self.num_cgra_col}"

def main():
    global_buffer = GlobalBuffer(4, 8)
    print(global_buffer.underlying)

if __name__ == "__main__":
    main()
