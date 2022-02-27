from kratos import Generator, always_comb, always_ff, posedge
from global_buffer.design.glb_tile_ifc import GlbTileInterface
from global_buffer.design.global_buffer_parameter import GlobalBufferParams


class GlbCfgCtrl(Generator):
    def __init__(self, _params: GlobalBufferParams):
        super().__init__("glb_cfg_ctrl")

        self._params = _params
        # local parameters

        config = GlbTileInterface(
            addr_width=self._params.axi_addr_width, data_width=self._params.axi_data_width)

        self.gclk = self.clock("gclk")
        self.mclk = self.clock("mclk")
        self.reset = self.reset("reset")
        self.glb_tile_id = self.input("glb_tile_id", _params.tile_sel_addr_width)

        # config port
        self.if_cfg_wst_s = self.interface(config.slave, "if_cfg_wst_s", is_port=True)
        self.if_cfg_est_m = self.interface(config.master, "if_cfg_est_m", is_port=True)

        self.h2d_pio_dec_write_data = self.output("h2d_pio_dec_write_data", _params.axi_data_width)
        self.h2d_pio_dec_address = self.output("h2d_pio_dec_address", _params.axi_addr_reg_width)
        self.h2d_pio_dec_read = self.output("h2d_pio_dec_read", 1)
        self.h2d_pio_dec_write = self.output("h2d_pio_dec_write", 1)

        self.d2h_dec_pio_read_data = self.input("d2h_dec_pio_read_data", _params.axi_data_width)
        self.d2h_dec_pio_ack = self.input("d2h_dec_pio_ack", 1)
        self.d2h_dec_pio_nack = self.input("d2h_dec_pio_nack", 1)

        # local variables
        self.if_cfg_wst_s_wr_clk_en_d = self.var("if_cfg_wst_s_wr_clk_en_d", 1)
        self.if_cfg_wst_s_rd_clk_en_d = self.var("if_cfg_wst_s_rd_clk_en_d", 1)
        self.if_cfg_est_m_wr_clk_en_sel_first_cycle = self.var("if_cfg_est_m_wr_clk_en_sel_first_cycle", 1)
        self.if_cfg_est_m_rd_clk_en_sel_first_cycle = self.var("if_cfg_est_m_rd_clk_en_sel_first_cycle", 1)
        self.if_cfg_est_m_wr_clk_en_sel_latch = self.var("if_cfg_est_m_wr_clk_en_sel_latch", 1)
        self.if_cfg_est_m_rd_clk_en_sel_latch = self.var("if_cfg_est_m_rd_clk_en_sel_latch", 1)
        self.if_cfg_est_m_wr_clk_en_sel = self.var("if_cfg_est_m_wr_clk_en_sel", 1)
        self.if_cfg_est_m_rd_clk_en_sel = self.var("if_cfg_est_m_rd_clk_en_sel", 1)
        self.wr_data_internal = self.var("wr_data_internal", _params.axi_data_width)
        self.addr_internal = self.var("addr_internal", _params.axi_addr_reg_width)
        self.read_internal = self.var("read_internal", 1)
        self.write_internal = self.var("write_internal", 1)
        self.rd_en_d1 = self.var("rd_en_d1", 1)
        self.rd_en_d2 = self.var("rd_en_d2", 1)
        self.rd_data_internal = self.var("rd_data_internal", _params.axi_data_width)
        self.rd_data_next = self.var("rd_data_next", _params.axi_data_width)
        self.rd_data_valid_internal = self.var("rd_data_valid_internal", 1)
        self.rd_data_valid_next = self.var("rd_data_vald_next", 1)
        self.wr_tile_id_match = self.var("wr_tile_id_match", 1)
        self.rd_tile_id_match = self.var("rd_tile_id_match", 1)

        self.tile_id_lsb = self._params.axi_addr_reg_width + self._params.axi_byte_offset
        self.tile_id_msb = self.tile_id_lsb + self._params.tile_sel_addr_width - 1

        self.add_always(self.tile_id_match)
        self.add_always(self.internal_logic)

        self.add_always(self.w2e_wr_ifc)
        self.add_always(self.w2e_rd_ifc)
        self.add_always(self.e2w_rd_ifc)
        self.add_always(self.rd_en_pipeline)
        self.add_always(self.rd_data_ff)
        self.add_always(self.clk_en_pipeline)
        self.add_always(self.est_m_clk_en_sel_first_cycle_comb)
        self.add_always(self.est_m_wr_clk_en_sel_latch)
        self.add_always(self.est_m_rd_clk_en_sel_latch)
        self.add_always(self.est_m_clk_en_sel_comb)
        self.add_always(self.est_m_wr_clk_en_mux)
        self.add_always(self.est_m_rd_clk_en_mux)

        # wire outputs
        self.wire_outputs()

    @always_comb
    def tile_id_match(self):
        self.wr_tile_id_match = self.glb_tile_id == self.if_cfg_wst_s.wr_addr[self.tile_id_msb, self.tile_id_lsb]
        self.rd_tile_id_match = self.glb_tile_id == self.if_cfg_wst_s.rd_addr[self.tile_id_msb, self.tile_id_lsb]

    @always_comb
    def internal_logic(self):
        self.wr_data_internal = 0
        self.addr_internal = 0
        self.read_internal = 0
        self.write_internal = 0
        if self.if_cfg_wst_s.rd_en and self.rd_tile_id_match:
            self.addr_internal = self.if_cfg_wst_s.rd_addr[(self._params.axi_byte_offset
                                                            + self._params.axi_addr_reg_width
                                                            - 1),
                                                           self._params.axi_byte_offset]
            self.read_internal = 1

        if self.if_cfg_wst_s.wr_en and self.wr_tile_id_match:
            self.addr_internal = self.if_cfg_wst_s.wr_addr[(self._params.axi_byte_offset
                                                            + self._params.axi_addr_reg_width
                                                            - 1),
                                                           self._params.axi_byte_offset]
            self.wr_data_internal = self.if_cfg_wst_s.wr_data
            self.write_internal = 1

    @always_ff((posedge, "gclk"), (posedge, "reset"))
    def rd_en_pipeline(self):
        if self.reset:
            self.rd_en_d1 = 0
            self.rd_en_d2 = 0
        else:
            self.rd_en_d1 = self.read_internal
            self.rd_en_d2 = self.rd_en_d1

    @always_ff((posedge, "gclk"), (posedge, "reset"))
    def rd_data_ff(self):
        if self.reset:
            self.rd_data_valid_internal = 0
            self.rd_data_internal = 0
        elif (self.rd_en_d2 == 1) & (self.d2h_dec_pio_ack | self.d2h_dec_pio_nack):
            self.rd_data_valid_internal = 1
            self.rd_data_internal = self.d2h_dec_pio_read_data
        else:
            self.rd_data_valid_internal = 0
            self.rd_data_internal = 0

    @always_ff((posedge, "gclk"), (posedge, "reset"))
    def w2e_wr_ifc(self):
        if self.reset:
            self.if_cfg_est_m.wr_en = 0
            self.if_cfg_est_m.wr_addr = 0
            self.if_cfg_est_m.wr_data = 0
        elif (~self.wr_tile_id_match and (self.if_cfg_wst_s.wr_en == 1)):
            # Passthrough cfg signals
            self.if_cfg_est_m.wr_en = self.if_cfg_wst_s.wr_en
            self.if_cfg_est_m.wr_addr = self.if_cfg_wst_s.wr_addr
            self.if_cfg_est_m.wr_data = self.if_cfg_wst_s.wr_data
        else:
            self.if_cfg_est_m.wr_en = 0
            self.if_cfg_est_m.wr_addr = 0
            self.if_cfg_est_m.wr_data = 0

    @always_ff((posedge, "gclk"), (posedge, "reset"))
    def w2e_rd_ifc(self):
        if self.reset:
            self.if_cfg_est_m.rd_en = 0
            self.if_cfg_est_m.rd_addr = 0
        elif (~self.rd_tile_id_match and (self.if_cfg_wst_s.rd_en == 1)):
            self.if_cfg_est_m.rd_en = self.if_cfg_wst_s.rd_en
            self.if_cfg_est_m.rd_addr = self.if_cfg_wst_s.rd_addr
        else:
            self.if_cfg_est_m.rd_en = 0
            self.if_cfg_est_m.rd_addr = 0

    @always_ff((posedge, "gclk"), (posedge, "reset"))
    def e2w_rd_ifc(self):
        if self.reset:
            self.if_cfg_wst_s.rd_data = 0
            self.if_cfg_wst_s.rd_data_valid = 0
        elif self.rd_data_valid_internal:
            self.if_cfg_wst_s.rd_data = self.rd_data_internal
            self.if_cfg_wst_s.rd_data_valid = self.rd_data_valid_internal
        else:
            self.if_cfg_wst_s.rd_data = self.if_cfg_est_m.rd_data
            self.if_cfg_wst_s.rd_data_valid = self.if_cfg_est_m.rd_data_valid

    def wire_outputs(self):
        # assign output wires
        self.wire(self.h2d_pio_dec_write_data, self.wr_data_internal)
        self.wire(self.h2d_pio_dec_address, self.addr_internal)
        self.wire(self.h2d_pio_dec_read, self.read_internal)
        self.wire(self.h2d_pio_dec_write, self.write_internal)

    @always_ff((posedge, "mclk"), (posedge, "reset"))
    def clk_en_pipeline(self):
        if self.reset:
            self.if_cfg_wst_s_wr_clk_en_d = 0
            self.if_cfg_wst_s_rd_clk_en_d = 0
        else:
            self.if_cfg_wst_s_wr_clk_en_d = self.if_cfg_wst_s.wr_clk_en
            self.if_cfg_wst_s_rd_clk_en_d = self.if_cfg_wst_s.rd_clk_en

    @always_comb
    def est_m_clk_en_sel_first_cycle_comb(self):
        self.if_cfg_est_m_wr_clk_en_sel_first_cycle = self.if_cfg_wst_s.wr_en & (~self.wr_tile_id_match)
        self.if_cfg_est_m_rd_clk_en_sel_first_cycle = self.if_cfg_wst_s.rd_en & (~self.rd_tile_id_match)

    @always_ff((posedge, "mclk"), (posedge, "reset"))
    def est_m_wr_clk_en_sel_latch(self):
        if self.reset:
            self.if_cfg_est_m_wr_clk_en_sel_latch = 0
        else:
            if self.if_cfg_wst_s.wr_en == 1:
                # If tile id matches, it does not feedthrough clk_en to the east
                if self.wr_tile_id_match:
                    self.if_cfg_est_m_wr_clk_en_sel_latch = 0
                else:
                    self.if_cfg_est_m_wr_clk_en_sel_latch = 1
            else:
                if self.if_cfg_wst_s.wr_clk_en == 0:
                    self.if_cfg_est_m_wr_clk_en_sel_latch = 0

    @always_ff((posedge, "mclk"), (posedge, "reset"))
    def est_m_rd_clk_en_sel_latch(self):
        if self.reset:
            self.if_cfg_est_m_rd_clk_en_sel_latch = 0
        else:
            if self.if_cfg_wst_s.rd_en == 1:
                # If tile id matches, it does not feedthrough clk_en to the east
                if self.rd_tile_id_match:
                    self.if_cfg_est_m_rd_clk_en_sel_latch = 0
                else:
                    self.if_cfg_est_m_rd_clk_en_sel_latch = 1
            else:
                if self.if_cfg_wst_s.rd_clk_en == 0:
                    self.if_cfg_est_m_rd_clk_en_sel_latch = 0

    @always_comb
    def est_m_clk_en_sel_comb(self):
        self.if_cfg_est_m_wr_clk_en_sel = (
            self.if_cfg_est_m_wr_clk_en_sel_first_cycle | self.if_cfg_est_m_wr_clk_en_sel_latch)
        self.if_cfg_est_m_rd_clk_en_sel = (
            self.if_cfg_est_m_rd_clk_en_sel_first_cycle | self.if_cfg_est_m_rd_clk_en_sel_latch)

    @always_comb
    def est_m_wr_clk_en_mux(self):
        if self.if_cfg_est_m_wr_clk_en_sel:
            self.if_cfg_est_m.wr_clk_en = self.if_cfg_wst_s_wr_clk_en_d
        else:
            self.if_cfg_est_m.wr_clk_en = 0

    @always_comb
    def est_m_rd_clk_en_mux(self):
        if self.if_cfg_est_m_rd_clk_en_sel:
            self.if_cfg_est_m.rd_clk_en = self.if_cfg_wst_s_rd_clk_en_d
        else:
            self.if_cfg_est_m.rd_clk_en = 0
