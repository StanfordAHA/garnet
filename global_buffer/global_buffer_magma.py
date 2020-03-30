import magma
from gemstone.generator.from_verilog import FromVerilog
from gemstone.generator.generator import Generator
from global_buffer.ifc_struct import *

class GlobalBuffer(Generator):
    def __init__(self, num_glb_tiles, num_cgra_col, banks_per_tile,
                 bank_addr_width, bank_data_width, cgra_data_width,
                 axi_addr_width, axi_data_width,
                 cfg_addr_width, cfg_data_width):

        super().__init__()

        self.num_glb_tiles = glb_tiles
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

        self.cgra_cfg_type = CgraCfgStruct(self.cfg_addr_width,
                                           self.cfg_data_width)

        self.add_ports(
            clk=magma.In(magma.Clock),
            reset=magma.In(magma.AsyncReset),
            stall=magma.In(magma.Bits[1]),

            proc_packet=ProcPacketIfc(self.glb_addr_width,
                                      self.bank_data_width).slave,
            glb_cfg=GlbCfgIfc(self.axi_addr_width,
                              self.axi_data_width).slave,
            sram_cfg=GlbCfgIfc(self.glb_addr_width,
                               self.axi_data_width).slave,

            stream_data_f2g=magma.In(
                magma.Array[self.num_glb_tiles*self.col_per_glb,
                            magma.Bits[self.cgra_data_width]]),
            stream_data_valid_f2g=magma.In(
                magma.Array[self.num_glb_tiles*self.col_per_glb,
                            magma.Bits[1]]),
            stream_data_g2f=magma.Out(
                magma.Array[self.num_glb_tiles*self.col_per_glb,
                            magma.Bits[self.cgra_data_width]]),
            stream_data_valid_g2f=magma.Out(
                magma.Array[self.num_glb_tiles*self.col_per_glb,
                            magma.Bits[1]]),

            cgra_cfg_jtag=magma.In(self.cgra_cfg_type),
            cgra_cfg_g2f=magma.Out(
                magma.Array[self.num_glb_tiles*self.col_per_glb,
                            self.cgra_cfg_type]),

            strm_start_pulse=magma.In(magma.Bits[self.num_glb_tiles]),
            pc_start_pulse=magma.In(magma.Bits[self.num_glb_tiles]),
            interrupt_pulse=magma.Out(magma.Bits[3*self.num_glb_tiles]),
        )

        self.underlying = FromVerilog(file_name="./global_buffer/rtl/global_buffer.sv")

    def name(self):
        return f"GlobalBuffer_{self.num_glb_tiles}_{self.num_cgra_col}"
