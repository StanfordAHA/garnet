from kratos import Generator
from global_buffer.design.glb_header import GlbHeader
from global_buffer.design.glb_cfg_ifc import GlbConfigInterface
from global_buffer.design.glb_tile_cfg_ctrl import GlbTileCfgCtrl
from global_buffer.gen_global_buffer_rdl import gen_global_buffer_rdl, gen_glb_pio_wrapper
from global_buffer.design.global_buffer_parameter import GlobalBufferParams
from systemRDL.util import run_systemrdl
import pathlib
import os


class GlbTileCfg(Generator):
    cache = None

    def __init__(self, _params: GlobalBufferParams):
        super().__init__("glb_tile_cfg")
        self._params = _params
        self.header = GlbHeader(self._params)
        cfg_ifc = GlbConfigInterface(addr_width=self._params.axi_addr_width, data_width=self._params.axi_data_width)

        # ports
        self.clk = self.clock("clk")
        self.reset = self.reset("reset", is_async=True)
        self.glb_tile_id = self.input("glb_tile_id", self._params.tile_sel_addr_width)

        # config port
        self.if_cfg_wst_s = self.interface(cfg_ifc.slave, "if_cfg_wst_s", is_port=True)
        self.if_cfg_est_m = self.interface(cfg_ifc.master, "if_cfg_est_m", is_port=True)

        # configuration register struct
        # TODO: Can we have a pass for this configuration?
        self.cfg_data_network = self.output("cfg_data_network", self.header.cfg_data_network_t)
        self.cfg_pcfg_network = self.output("cfg_pcfg_network", self.header.cfg_pcfg_network_t)

        # st dma
        self.cfg_st_dma_ctrl = self.output("cfg_st_dma_ctrl", self.header.cfg_dma_ctrl_t)

        self.cfg_st_dma_header = self.output("cfg_st_dma_header", self.header.cfg_dma_header_t,
                                             size=self._params.queue_depth)
        # ld dma
        self.cfg_ld_dma_ctrl = self.output("cfg_ld_dma_ctrl", self.header.cfg_dma_ctrl_t)

        self.cfg_ld_dma_header = self.output("cfg_ld_dma_header", self.header.cfg_dma_header_t,
                                             size=self._params.queue_depth)

        # pcfg dma
        self.cfg_pcfg_dma_ctrl = self.output("cfg_pcfg_dma_ctrl", self.header.cfg_pcfg_dma_ctrl_t)
        self.cfg_pcfg_dma_header = self.output("cfg_pcfg_dma_header", self.header.cfg_pcfg_dma_header_t)

        self.glb_pio_wrapper = self.get_glb_pio_wrapper()
        # TODO: Update axi_reg_addr_width
        self.add_child("glb_pio", self.glb_pio_wrapper)
        self.glb_tile_cfg_ctrl = GlbTileCfgCtrl(self._params)
        self.add_child("glb_tile_cfg_ctrl", self.glb_tile_cfg_ctrl)

        self.wire_config_signals()
        self.wire_ctrl_signals()

    def get_glb_pio_wrapper(self):
        # TODO: For now, we run systemRDL to generate SV and parse it.
        # However, in the future, we need to generate wrapper directly from configuration space.
        top_name = "glb"
        garnet_home = pathlib.Path(__file__).parent.parent.parent.resolve()
        rdl_output_folder = os.path.join(garnet_home, "global_buffer/systemRDL/output/")
        pio_file = rdl_output_folder + top_name + "_pio.sv"
        pio_wrapper_file = rdl_output_folder + top_name + "_pio_wrapper.sv"

        if not self.__class__.cache:
            self.__class__.cache = self._params
            glb_rdl = gen_global_buffer_rdl(name=top_name, params=self._params)

            # Dump rdl file
            rdl_file = os.path.join(garnet_home, "global_buffer/systemRDL/glb.rdl")
            glb_rdl.dump_rdl(rdl_file)

            # Run ORDT to generate RTL
            ordt_path = os.path.join(garnet_home, 'systemRDL', 'Ordt.jar')
            rdl_parms_file = os.path.join(garnet_home, "global_buffer/systemRDL/ordt_params/glb.parms")
            run_systemrdl(ordt_path, top_name, rdl_file, rdl_parms_file, rdl_output_folder)

            # Create wrapper of glb_pio.sv
            gen_glb_pio_wrapper(src_file=pio_file, dest_file=pio_wrapper_file)

        return self.from_verilog("glb_pio", pio_wrapper_file, [], {})

    def wire_config_signals(self):
        self.wire(self.clk, self.glb_pio_wrapper.ports["clk"])
        self.wire(self.reset, self.glb_pio_wrapper.ports["reset"])
        self.wire(self.cfg_data_network['tile_connected'],
                  self.glb_pio_wrapper.ports[f"l2h_data_network_tile_connected_r"])
        self.wire(self.cfg_data_network['latency'],
                  self.glb_pio_wrapper.ports[f"l2h_data_network_latency_r"])

        self.wire(self.cfg_pcfg_network['tile_connected'],
                  self.glb_pio_wrapper.ports[f"l2h_pcfg_network_tile_connected_r"])
        self.wire(self.cfg_pcfg_network['latency'],
                  self.glb_pio_wrapper.ports[f"l2h_pcfg_network_latency_r"])

        self.wire(self.cfg_st_dma_ctrl['data_mux'],
                  self.glb_pio_wrapper.ports[f"l2h_st_dma_ctrl_data_mux_r"])
        self.wire(self.cfg_st_dma_ctrl['mode'], self.glb_pio_wrapper.ports[f"l2h_st_dma_ctrl_mode_r"])
        self.wire(self.cfg_st_dma_ctrl['use_valid'],
                  self.glb_pio_wrapper.ports[f"l2h_st_dma_ctrl_use_valid_r"])
        self.wire(self.cfg_st_dma_ctrl['num_repeat'], self.glb_pio_wrapper.ports[f"l2h_st_dma_ctrl_num_repeat_r"])

        for i in range(self._params.queue_depth):
            if self._params.queue_depth == 1:
                current_header = self.cfg_st_dma_header
            else:
                current_header = self.cfg_st_dma_header[i]
            self.wire(current_header['start_addr'],
                      self.glb_pio_wrapper.ports[f"l2h_st_dma_header_{i}_start_addr_start_addr_r"])
            self.wire(current_header['cycle_start_addr'],
                      self.glb_pio_wrapper.ports[f"l2h_st_dma_header_{i}_cycle_start_addr_cycle_start_addr_r"])
            self.wire(current_header['dim'],
                      self.glb_pio_wrapper.ports[f"l2h_st_dma_header_{i}_dim_dim_r"])
            for j in range(self._params.loop_level):
                self.wire(current_header[f"cycle_stride_{j}"],
                          self.glb_pio_wrapper.ports[f"l2h_st_dma_header_{i}_cycle_stride_{j}_cycle_stride_r"])
                self.wire(current_header[f"stride_{j}"],
                          self.glb_pio_wrapper.ports[f"l2h_st_dma_header_{i}_stride_{j}_stride_r"])
                self.wire(current_header[f"range_{j}"],
                          self.glb_pio_wrapper.ports[f"l2h_st_dma_header_{i}_range_{j}_range_r"])

        self.wire(self.cfg_ld_dma_ctrl['data_mux'],
                  self.glb_pio_wrapper.ports[f"l2h_ld_dma_ctrl_data_mux_r"])
        self.wire(self.cfg_ld_dma_ctrl['mode'], self.glb_pio_wrapper.ports[f"l2h_ld_dma_ctrl_mode_r"])
        self.wire(self.cfg_ld_dma_ctrl['use_valid'],
                  self.glb_pio_wrapper.ports[f"l2h_ld_dma_ctrl_use_valid_r"])
        self.wire(self.cfg_ld_dma_ctrl['num_repeat'], self.glb_pio_wrapper.ports[f"l2h_ld_dma_ctrl_num_repeat_r"])

        for i in range(self._params.queue_depth):
            if self._params.queue_depth == 1:
                current_header = self.cfg_ld_dma_header
            else:
                current_header = self.cfg_ld_dma_header[i]
            self.wire(current_header['start_addr'],
                      self.glb_pio_wrapper.ports[f"l2h_ld_dma_header_{i}_start_addr_start_addr_r"])
            self.wire(current_header['cycle_start_addr'],
                      self.glb_pio_wrapper.ports[f"l2h_ld_dma_header_{i}_cycle_start_addr_cycle_start_addr_r"])
            self.wire(current_header['dim'],
                      self.glb_pio_wrapper.ports[f"l2h_ld_dma_header_{i}_dim_dim_r"])
            for j in range(self._params.loop_level):
                self.wire(current_header[f"cycle_stride_{j}"],
                          self.glb_pio_wrapper.ports[f"l2h_ld_dma_header_{i}_cycle_stride_{j}_cycle_stride_r"])
                self.wire(current_header[f"stride_{j}"],
                          self.glb_pio_wrapper.ports[f"l2h_ld_dma_header_{i}_stride_{j}_stride_r"])
                self.wire(current_header[f"range_{j}"],
                          self.glb_pio_wrapper.ports[f"l2h_ld_dma_header_{i}_range_{j}_range_r"])

        self.wire(
            self.cfg_pcfg_dma_ctrl['mode'], self.glb_pio_wrapper.ports[f"l2h_pcfg_dma_ctrl_mode_r"])

        self.wire(self.cfg_pcfg_dma_header['start_addr'],
                  self.glb_pio_wrapper.ports[f"l2h_pcfg_dma_header_start_addr_start_addr_r"])
        self.wire(self.cfg_pcfg_dma_header['num_cfg'],
                  self.glb_pio_wrapper.ports[f"l2h_pcfg_dma_header_num_cfg_num_cfg_r"])

    def wire_ctrl_signals(self):
        self.wire(self.clk, self.glb_tile_cfg_ctrl.clk)
        self.wire(self.reset, self.glb_tile_cfg_ctrl.reset)
        self.wire(self.glb_tile_id, self.glb_tile_cfg_ctrl.glb_tile_id)
        self.wire(self.if_cfg_wst_s, self.glb_tile_cfg_ctrl.if_cfg_wst_s)
        self.wire(self.if_cfg_est_m, self.glb_tile_cfg_ctrl.if_cfg_est_m)

        self.wire(self.glb_pio_wrapper.ports['h2d_pio_dec_address'],
                  self.glb_tile_cfg_ctrl.h2d_pio_dec_address)
        self.wire(self.glb_pio_wrapper.ports['h2d_pio_dec_write_data'],
                  self.glb_tile_cfg_ctrl.h2d_pio_dec_write_data)
        self.wire(self.glb_pio_wrapper.ports['h2d_pio_dec_write'],
                  self.glb_tile_cfg_ctrl.h2d_pio_dec_write)
        self.wire(
            self.glb_pio_wrapper.ports['h2d_pio_dec_read'], self.glb_tile_cfg_ctrl.h2d_pio_dec_read)
        self.wire(self.glb_pio_wrapper.ports['d2h_dec_pio_read_data'],
                  self.glb_tile_cfg_ctrl.d2h_dec_pio_read_data)
        self.wire(self.glb_pio_wrapper.ports['d2h_dec_pio_ack'],
                  self.glb_tile_cfg_ctrl.d2h_dec_pio_ack)
        self.wire(self.glb_pio_wrapper.ports['d2h_dec_pio_nack'],
                  self.glb_tile_cfg_ctrl.d2h_dec_pio_nack)
