from kratos import Generator, always_comb
from global_buffer.design.glb_header import GlbHeader
from global_buffer.design.glb_cfg_ifc import GlbConfigInterface
from global_buffer.design.glb_tile_cfg_ctrl import GlbTileCfgCtrl
from global_buffer.design.glb_pio_wrapper import GlbPioWrapper
from global_buffer.design.global_buffer_parameter import GlobalBufferParams


class GlbTileCfg(Generator):
    def __init__(self, _params: GlobalBufferParams):
        super().__init__("glb_tile_cfg")
        self._params = _params
        self.header = GlbHeader(self._params)
        cfg_ifc = GlbConfigInterface(
            addr_width=self._params.axi_addr_width, data_width=self._params.axi_data_width)

        # ports
        self.clk = self.clock("clk")
        self.reset = self.reset("reset", is_async=True)
        self.glb_tile_id = self.input(
            "glb_tile_id", self._params.tile_sel_addr_width)

        # config port
        self.if_cfg_wst_s = self.interface(
            cfg_ifc.slave, "if_cfg_wst_s", is_port=True)
        self.if_cfg_est_m = self.interface(
            cfg_ifc.master, "if_cfg_est_m", is_port=True)

        # configuration register struct
        # TODO: Can we have a pass for this configuration?
        # TODO: Can we dump configuration struct verilog as external file?
        self.cfg_data_network = self.output(
            "cfg_data_network", self.header.cfg_data_network_t)

        self.cfg_pcfg_network = self.output(
            "cfg_pcfg_network", self.header.cfg_pcfg_network_t)

        # st dma
        self.cfg_st_dma_ctrl = self.output(
            "cfg_st_dma_ctrl", self.header.cfg_st_dma_ctrl_t)

        self.cfg_st_dma_header = self.output("cfg_st_dma_header", self.header.cfg_st_dma_header_t,
                                             size=self._params.queue_depth)
        self.st_dma_header_clr = self.input(
            "st_dma_header_clr", width=self._params.queue_depth)

        # ld dma
        self.cfg_ld_dma_ctrl = self.output(
            "cfg_ld_dma_ctrl", self.header.cfg_ld_dma_ctrl_t)

        self.cfg_ld_dma_header = self.output("cfg_ld_dma_header", self.header.cfg_ld_dma_header_t,
                                             size=self._params.queue_depth)
        self.ld_dma_header_clr = self.input(
            "ld_dma_header_clr", width=self._params.queue_depth)

        # pcfg dma
        self.cfg_pcfg_dma_ctrl = self.output(
            "cfg_pcfg_dma_ctrl", self.header.cfg_pcfg_dma_ctrl_t)
        self.cfg_pcfg_dma_header = self.output(
            "cfg_pcfg_dma_header", self.header.cfg_pcfg_dma_header_t)

        # TODO: For now, we parse generated glb_pio.sv file. Later this should be auto generated from RDL
        self.glb_pio_wrapper = GlbPioWrapper()
        self.add_child("glb_pio", self.glb_pio_wrapper)
        self.glb_tile_cfg_ctrl = GlbTileCfgCtrl(self._params)
        self.add_child("glb_tile_cfg_ctrl", self.glb_tile_cfg_ctrl)

        self.wire_config_signals()
        self.wire_ctrl_signals()

    def wire_config_signals(self):
        self.wire(self.clk, self.glb_pio_wrapper.ports["clk"])
        self.wire(self.reset, self.glb_pio_wrapper.ports["reset"])
        self.wire(self.cfg_data_network['f2g_mux'],
                  self.glb_pio_wrapper.ports[f"l2h_data_network_f2g_mux_r"])
        self.wire(self.cfg_data_network['g2f_mux'],
                  self.glb_pio_wrapper.ports[f"l2h_data_network_g2f_mux_r"])
        self.wire(self.cfg_data_network['tile_connected'],
                  self.glb_pio_wrapper.ports[f"l2h_data_network_tile_connected_r"])
        self.wire(self.cfg_data_network['latency'],
                  self.glb_pio_wrapper.ports[f"l2h_data_network_latency_r"])

        self.wire(self.cfg_pcfg_network['tile_connected'],
                  self.glb_pio_wrapper.ports[f"l2h_pcfg_network_tile_connected_r"])
        self.wire(self.cfg_pcfg_network['latency'],
                  self.glb_pio_wrapper.ports[f"l2h_pcfg_network_latency_r"])

        self.wire(
            self.cfg_st_dma_ctrl['mode'], self.glb_pio_wrapper.ports[f"l2h_st_dma_ctrl_mode_r"])

        if self._params.queue_depth == 1:
            self.wire(self.cfg_st_dma_header[0]['validate'],
                      self.glb_pio_wrapper.ports[f"l2h_st_dma_header_validate_validate_r"])
            self.wire(self.cfg_st_dma_header[0]['start_addr'],
                      self.glb_pio_wrapper.ports[f"l2h_st_dma_header_start_addr_start_addr_r"])
            self.wire(self.cfg_st_dma_header[0]['num_words'],
                      self.glb_pio_wrapper.ports[f"l2h_st_dma_header_num_words_num_words_r"])
            self.wire(self.st_dma_header_clr[0],
                      self.glb_pio_wrapper.ports[f"h2l_st_dma_header_validate_validate_hwclr"])
        else:
            for i in range(self._params.queue_depth):
                self.wire(self.cfg_st_dma_header[i]['validate'],
                          self.glb_pio_wrapper.ports[f"l2h_st_dma_header_{i}_validate_validate_r"])
                self.wire(self.cfg_st_dma_header[i]['start_addr'],
                          self.glb_pio_wrapper.ports[f"l2h_st_dma_header_{i}_start_addr_start_addr_r"])
                self.wire(self.cfg_st_dma_header[i]['num_words'],
                          self.glb_pio_wrapper.ports[f"l2h_st_dma_header_{i}_num_words_num_words_r"])
                self.wire(self.st_dma_header_clr[i],
                          self.glb_pio_wrapper.ports[f"h2l_st_dma_header_{i}_validate_validate_hwclr"])

        self.wire(
            self.cfg_ld_dma_ctrl['mode'], self.glb_pio_wrapper.ports[f"l2h_ld_dma_ctrl_mode_r"])
        self.wire(self.cfg_ld_dma_ctrl['use_valid'],
                  self.glb_pio_wrapper.ports[f"l2h_ld_dma_ctrl_use_valid_r"])

        if self._params.queue_depth == 1:
            self.wire(self.cfg_ld_dma_header[0]['validate'],
                      self.glb_pio_wrapper.ports[f"l2h_ld_dma_header_validate_validate_r"])
            self.wire(self.cfg_ld_dma_header[0]['start_addr'],
                      self.glb_pio_wrapper.ports[f"l2h_ld_dma_header_start_addr_start_addr_r"])
            for j in range(self._params.loop_level):
                self.wire(
                    self.cfg_ld_dma_header[0][f"stride_{j}"], self.glb_pio_wrapper.ports[f"l2h_ld_dma_header_stride_{j}_stride_r"])
                self.wire(
                    self.cfg_ld_dma_header[0][f"range_{j}"], self.glb_pio_wrapper.ports[f"l2h_ld_dma_header_range_{j}_range_r"])
            self.wire(self.cfg_ld_dma_header[0]['num_active_words'],
                      self.glb_pio_wrapper.ports[f"l2h_ld_dma_header_num_active_words_num_active_words_r"])
            self.wire(self.cfg_ld_dma_header[0]['num_inactive_words'],
                      self.glb_pio_wrapper.ports[f"l2h_ld_dma_header_num_inactive_words_num_inactive_words_r"])
            self.wire(self.ld_dma_header_clr[0],
                      self.glb_pio_wrapper.ports[f"h2l_ld_dma_header_validate_validate_hwclr"])
        else:
            for i in range(self._params.queue_depth):
                self.wire(self.cfg_ld_dma_header[i]['validate'],
                          self.glb_pio_wrapper.ports[f"l2h_ld_dma_header_{i}_validate_validate_r"])
                self.wire(self.cfg_ld_dma_header[i]['start_addr'],
                          self.glb_pio_wrapper.ports[f"l2h_ld_dma_header_{i}_start_addr_start_addr_r"])
                for j in range(self._params.loop_level):
                    self.wire(
                        self.cfg_ld_dma_header[i][f"stride_{j}"], self.glb_pio_wrapper.ports[f"l2h_ld_dma_header_{i}_stride_{j}_stride_r"])
                    self.wire(
                        self.cfg_ld_dma_header[i][f"range_{j}"], self.glb_pio_wrapper.ports[f"l2h_ld_dma_header_{i}_range_{j}_range_r"])
                self.wire(self.cfg_ld_dma_header[i]['num_active_words'],
                          self.glb_pio_wrapper.ports[f"l2h_ld_dma_header_{i}_num_active_words_num_active_words_r"])
                self.wire(self.cfg_ld_dma_header[i]['num_inactive_words'],
                          self.glb_pio_wrapper.ports[f"l2h_ld_dma_header_{i}_num_inactive_words_num_inactive_words_r"])
                self.wire(self.ld_dma_header_clr[i],
                          self.glb_pio_wrapper.ports[f"h2l_ld_dma_header_{i}_validate_validate_hwclr"])

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

        # TODO: Use portbundle for systemrdl specific ports
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
