import magma
from gemstone.common.jtag_type import JTAGType
from gemstone.common.configurable import ConfigurationType
from gemstone.generator.from_magma import FromMagma
from gemstone.generator.generator import Generator
from gemstone.generator.const import Const
from .global_controller_genesis2 import gen_wrapper, GlobalControllerParams
from cgra.ifc_struct import *
from systemRDL.util import run_systemrdl
import pathlib
import os
import math


class GlobalController(Generator):
    cache = None

    def __init__(self, addr_width=32, data_width=32,
                 axi_addr_width=12, axi_data_width=32,
                 num_glb_tiles=16, cgra_width=32, glb_addr_width=22,
                 block_axi_addr_width=12, glb_tile_mem_size=256, group_size=4):
        super().__init__()

        self.addr_width = addr_width
        self.data_width = data_width
        self.axi_addr_width = axi_addr_width
        self.axi_data_width = axi_data_width
        self.num_glb_tiles = num_glb_tiles
        self.cgra_width = cgra_width
        self.glb_addr_width = glb_addr_width
        self.glb_tile_mem_size = glb_tile_mem_size
        self.block_axi_addr_width = block_axi_addr_width
        self.group_size = group_size
        # Control logic assumes cgra config_data_width is same as axi_data_width
        assert self.axi_data_width == self.data_width

        self.config_type = ConfigurationType(self.addr_width, self.data_width)

        self.add_ports(
            clk_in=magma.In(magma.Clock),
            reset_in=magma.In(magma.AsyncReset),

            clk_out=magma.Out(magma.Clock),
            reset_out=magma.Out(magma.AsyncReset),
            cgra_stall=magma.Out(magma.Bits[self.cgra_width]),
            glb_clk_en_master=magma.Out(magma.Bits[self.num_glb_tiles]),
            glb_clk_en_bank_master=magma.Out(magma.Bits[self.num_glb_tiles]),
            glb_pcfg_broadcast_stall=magma.Out(magma.Bits[self.num_glb_tiles]),
            glb_flush_crossbar_sel=magma.Out(magma.Bits[math.ceil(
                math.log(self.num_glb_tiles, 2)) * self.cgra_width // self.group_size]),

            glb_cfg=GlbCfgIfc(self.block_axi_addr_width,
                              self.axi_data_width).master,
            sram_cfg=GlbCfgIfc(self.glb_addr_width, self.axi_data_width, is_clk_en=False).master,

            strm_g2f_start_pulse=magma.Out(magma.Bits[self.num_glb_tiles]),
            strm_f2g_start_pulse=magma.Out(magma.Bits[self.num_glb_tiles]),
            pc_start_pulse=magma.Out(magma.Bits[self.num_glb_tiles]),
            strm_g2f_interrupt_pulse=magma.In(magma.Bits[self.num_glb_tiles]),
            strm_f2g_interrupt_pulse=magma.In(magma.Bits[self.num_glb_tiles]),
            pcfg_g2f_interrupt_pulse=magma.In(magma.Bits[self.num_glb_tiles]),

            cgra_config=magma.Out(self.config_type),
            read_data_in=magma.In(magma.Bits[self.data_width]),
            jtag=JTAGType,
            axi4_slave=AXI4LiteIfc(self.axi_addr_width, self.data_width).slave,
            interrupt=magma.Out(magma.Bit)
        )

        if not self.__class__.cache:
            self.__class__.cache = 1
            self.run_glc_systemrdl()

        params = GlobalControllerParams(cfg_data_width=self.data_width,
                                        cfg_addr_width=self.addr_width,
                                        axi_addr_width=self.axi_addr_width,
                                        axi_data_width=self.axi_data_width,
                                        num_glb_tiles=self.num_glb_tiles,
                                        cgra_width=self.cgra_width,
                                        glb_tile_mem_size=self.glb_tile_mem_size,
                                        block_axi_addr_width=self.block_axi_addr_width)

        wrapper = gen_wrapper(params)
        generator = wrapper.generator(mode="declare")
        self.underlying = FromMagma(generator())

        # wire clk and reset
        self.wire(self.ports.clk_in, self.underlying.ports.clk_in)
        self.wire(self.ports.reset_in, self.underlying.ports.reset_in)

        # cgra control signals
        self.wire(self.underlying.ports.clk_out, self.ports.clk_out)
        self.wire(self.underlying.ports.reset_out, self.ports.reset_out)
        self.wire(self.underlying.ports.cgra_stall, self.ports.cgra_stall)
        self.wire(self.underlying.ports.glb_clk_en_master, self.ports.glb_clk_en_master)
        self.wire(self.underlying.ports.glb_clk_en_bank_master, self.ports.glb_clk_en_bank_master)
        self.wire(self.underlying.ports.glb_pcfg_broadcast_stall, self.ports.glb_pcfg_broadcast_stall)
        self.wire(self.underlying.ports.glb_flush_crossbar_sel, self.ports.glb_flush_crossbar_sel)

        # global buffer configuration
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
        self.wire(self.underlying.ports.glb_cfg_rd_data,
                  self.ports.glb_cfg.rd_data)
        self.wire(self.underlying.ports.glb_cfg_rd_data_valid,
                  self.ports.glb_cfg.rd_data_valid)

        # global buffer sram configuration
        self.wire(self.ports.sram_cfg.wr_en,
                  self.underlying.ports.sram_cfg_wr_en)
        self.wire(self.ports.sram_cfg.wr_addr,
                  self.underlying.ports.sram_cfg_wr_addr)
        self.wire(self.ports.sram_cfg.wr_data,
                  self.underlying.ports.sram_cfg_wr_data)
        self.wire(self.ports.sram_cfg.rd_en,
                  self.underlying.ports.sram_cfg_rd_en)
        self.wire(self.ports.sram_cfg.rd_addr,
                  self.underlying.ports.sram_cfg_rd_addr)
        self.wire(self.underlying.ports.sram_cfg_rd_data,
                  self.ports.sram_cfg.rd_data)
        self.wire(self.underlying.ports.sram_cfg_rd_data_valid,
                  self.ports.sram_cfg.rd_data_valid)

        # start/done pulse
        self.wire(self.underlying.ports.strm_f2g_interrupt_pulse,
                  self.ports.strm_f2g_interrupt_pulse)
        self.wire(self.underlying.ports.strm_g2f_interrupt_pulse,
                  self.ports.strm_g2f_interrupt_pulse)
        self.wire(self.underlying.ports.pcfg_g2f_interrupt_pulse,
                  self.ports.pcfg_g2f_interrupt_pulse)
        self.wire(self.ports.strm_g2f_start_pulse,
                  self.underlying.ports.strm_g2f_start_pulse)
        self.wire(self.ports.strm_f2g_start_pulse,
                  self.underlying.ports.strm_f2g_start_pulse)
        self.wire(self.ports.pc_start_pulse,
                  self.underlying.ports.pc_start_pulse)

        # cgra configuration interface
        self.wire(self.underlying.ports.cgra_cfg_addr,
                  self.ports.cgra_config.config_addr)
        self.wire(self.underlying.ports.cgra_cfg_wr_data,
                  self.ports.cgra_config.config_data)
        self.wire(self.underlying.ports.cgra_cfg_read,
                  self.ports.cgra_config.read[0])
        self.wire(self.underlying.ports.cgra_cfg_write,
                  self.ports.cgra_config.write[0])
        self.wire(self.ports.read_data_in,
                  self.underlying.ports.cgra_cfg_rd_data)

        # axi4-lite slave interface
        self.wire(self.ports.axi4_slave.awaddr,
                  self.underlying.ports.axi_awaddr)
        self.wire(self.ports.axi4_slave.awvalid,
                  self.underlying.ports.axi_awvalid)
        self.wire(self.ports.axi4_slave.awready,
                  self.underlying.ports.axi_awready)
        self.wire(self.ports.axi4_slave.wdata,
                  self.underlying.ports.axi_wdata)
        self.wire(self.ports.axi4_slave.wvalid,
                  self.underlying.ports.axi_wvalid)
        self.wire(self.ports.axi4_slave.wready,
                  self.underlying.ports.axi_wready)
        self.wire(self.ports.axi4_slave.bready,
                  self.underlying.ports.axi_bready)
        self.wire(self.ports.axi4_slave.bvalid,
                  self.underlying.ports.axi_bvalid)
        self.wire(self.ports.axi4_slave.bresp,
                  self.underlying.ports.axi_bresp)
        self.wire(self.ports.axi4_slave.araddr,
                  self.underlying.ports.axi_araddr)
        self.wire(self.ports.axi4_slave.arvalid,
                  self.underlying.ports.axi_arvalid)
        self.wire(self.ports.axi4_slave.arready,
                  self.underlying.ports.axi_arready)
        self.wire(self.ports.axi4_slave.rdata,
                  self.underlying.ports.axi_rdata)
        self.wire(self.ports.axi4_slave.rresp,
                  self.underlying.ports.axi_rresp)
        self.wire(self.ports.axi4_slave.rvalid,
                  self.underlying.ports.axi_rvalid)
        self.wire(self.ports.axi4_slave.rready,
                  self.underlying.ports.axi_rready)

        # interrupt
        self.wire(self.ports.interrupt, self.underlying.ports.interrupt)

        # jtag interface signals
        self.wire(self.ports.jtag.tdi, self.underlying.ports.tdi)
        self.wire(self.ports.jtag.tdo, self.underlying.ports.tdo)
        self.wire(self.ports.jtag.tms, self.underlying.ports.tms)
        self.wire(self.ports.jtag.tck, self.underlying.ports.tck)
        self.wire(self.ports.jtag.trst_n, self.underlying.ports.trst_n)

    def name(self):
        return f"GlobalController_cfg_{self.addr_width}_{self.data_width}" \
               f"_axi_{self.axi_addr_width}_{self.axi_data_width}"

    def run_glc_systemrdl(self):
        top_name = "glc"
        garnet_home = pathlib.Path(__file__).parent.parent.resolve()

        rdl_file = os.path.join(garnet_home, 'global_controller/systemRDL/rdl_models/glc.rdl.final')
        rdl_output_folder = os.path.join(garnet_home, 'global_controller/systemRDL/output/')
        # Run perl preprocessing
        os.system(f"{os.path.join(garnet_home, 'systemRDL', 'perlpp.pl')}"
                  f" {os.path.join(garnet_home, 'global_controller/systemRDL/rdl_models/glc.rdl')}"
                  f" -o {rdl_file}")

        # Run ORDT to generate RTL
        ordt_path = os.path.join(garnet_home, 'systemRDL', 'Ordt.jar')
        rdl_parms_file = os.path.join(garnet_home, "global_controller/systemRDL/ordt_params/glc.parms")
        run_systemrdl(ordt_path, top_name, rdl_file, rdl_parms_file, rdl_output_folder)
