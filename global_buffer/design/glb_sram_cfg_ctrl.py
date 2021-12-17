from kratos import Generator, always_ff, always_comb, posedge
from global_buffer.design.global_buffer_parameter import GlobalBufferParams
from global_buffer.design.glb_cfg_ifc import GlbConfigInterface
from global_buffer.design.glb_header import GlbHeader


class GlbSramCfgCtrl(Generator):
    def __init__(self, _params: GlobalBufferParams):
        super().__init__("glb_sram_cfg_ctrl")
        self._params = _params
        self.header = GlbHeader(self._params)

        self.clk = self.clock("clk")
        self.reset = self.reset("reset")
        self.glb_tile_id = self.input("glb_tile_id", self._params.tile_sel_addr_width)

        self.sram_cfg_ifc = GlbConfigInterface(addr_width=self._params.glb_addr_width,
                                               data_width=self._params.axi_data_width)
        self.bank_cfg_ifc = GlbConfigInterface(addr_width=self._params.bank_addr_width,
                                               data_width=self._params.axi_data_width)

        # config port
        self.if_sram_cfg_est_m = self.interface(self.sram_cfg_ifc.master, "if_sram_cfg_est_m", is_port=True)
        self.if_sram_cfg_wst_s = self.interface(self.sram_cfg_ifc.slave, "if_sram_cfg_wst_s", is_port=True)

        # bank_config port
        self.if_sram_cfg_ctrl2bank_m = []
        for i in range(self._params.banks_per_tile):
            self.if_sram_cfg_ctrl2bank_m.append(self.interface(
                self.bank_cfg_ifc.master, f"if_sram_cfg_ctrl2bank_m_{i}", is_port=True))

        # local variables
        self.if_sram_cfg_est_m_wr_en_w = self.var("if_sram_cfg_est_m_wr_en_w", 1)
        self.if_sram_cfg_est_m_wr_addr_w = self.var("if_sram_cfg_est_m_wr_addr_w", self._params.glb_addr_width)
        self.if_sram_cfg_est_m_wr_data_w = self.var("if_sram_cfg_est_m_wr_data_w", self._params.axi_data_width)
        self.if_sram_cfg_est_m_rd_en_w = self.var("if_sram_cfg_est_m_rd_en_w", 1)
        self.if_sram_cfg_est_m_rd_addr_w = self.var("if_sram_cfg_est_m_rd_addr_w", self._params.glb_addr_width)

        self.ctrl2bank_m_wr_en_w = self.var("ctrl2bank_m_wr_en_w", 1, size=self._params.banks_per_tile)
        self.ctrl2bank_m_wr_addr_w = self.var(
            "ctrl2bank_m_wr_addr_w", self._params.bank_addr_width, size=self._params.banks_per_tile)
        self.ctrl2bank_m_wr_data_w = self.var(
            "ctrl2bank_m_wr_data_w", self._params.axi_data_width, size=self._params.banks_per_tile)
        self.ctrl2bank_m_rd_en_w = self.var("ctrl2bank_m_rd_en_w", 1, size=self._params.banks_per_tile)
        self.ctrl2bank_m_rd_addr_w = self.var(
            "ctrl2bank_m_rd_addr_w", self._params.bank_addr_width, size=self._params.banks_per_tile)

        self.wr_tile_id_match = self.var("wr_tile_id_match", 1)
        self.rd_tile_id_match = self.var("rd_tile_id_match", 1)
        self.wr_bank_sel = self.var("wr_bank_sel", self._params.bank_sel_addr_width)
        self.rd_bank_sel = self.var("rd_bank_sel", self._params.bank_sel_addr_width)
        self.rd_data_valid_w = self.var("rd_data_valid_w", 1)
        self.rd_data_w = self.var("rd_data_w", self._params.axi_data_width)

        # local pararmeters
        self.tile_id_lsb = self._params.bank_addr_width + self._params.bank_sel_addr_width
        self.tile_id_msb = self.tile_id_lsb + self._params.tile_sel_addr_width - 1
        self.bank_sel_lsb = self._params.bank_addr_width
        self.bank_sel_msb = self.bank_sel_lsb + self._params.bank_sel_addr_width - 1

        self.add_always(self.tile_id_match)
        self.add_always(self.wr_logic)
        self.add_always(self.rdrq_logic)
        self.add_always(self.rdrs_logic)
        self.add_always(self.pipeline)

    @always_comb
    def tile_id_match(self):
        self.wr_tile_id_match = self.glb_tile_id == self.if_sram_cfg_wst_s.wr_addr[self.tile_id_msb, self.tile_id_lsb]
        self.rd_tile_id_match = self.glb_tile_id == self.if_sram_cfg_wst_s.rd_addr[self.tile_id_msb, self.tile_id_lsb]

    @always_comb
    def wr_logic(self):
        self.wr_bank_sel = self.if_sram_cfg_wst_s.wr_addr[self.bank_sel_msb, self.bank_sel_lsb]
        if self.if_sram_cfg_wst_s.wr_en:
            if self.wr_tile_id_match:
                self.if_sram_cfg_est_m_wr_en_w = 0
                self.if_sram_cfg_est_m_wr_addr_w = 0
                self.if_sram_cfg_est_m_wr_data_w = 0
                for i in range(self._params.banks_per_tile):
                    if self.wr_bank_sel == i:
                        self.ctrl2bank_m_wr_en_w[i] = self.if_sram_cfg_wst_s.wr_en
                        self.ctrl2bank_m_wr_addr_w[i] = self.if_sram_cfg_wst_s.wr_addr[self._params.bank_addr_width - 1,
                                                                                       0]
                        self.ctrl2bank_m_wr_data_w[i] = self.if_sram_cfg_wst_s.wr_data
                    else:
                        self.ctrl2bank_m_wr_en_w[i] = 0
                        self.ctrl2bank_m_wr_addr_w[i] = 0
                        self.ctrl2bank_m_wr_data_w[i] = 0
            else:
                self.if_sram_cfg_est_m_wr_en_w = self.if_sram_cfg_wst_s.wr_en
                self.if_sram_cfg_est_m_wr_addr_w = self.if_sram_cfg_wst_s.wr_addr
                self.if_sram_cfg_est_m_wr_data_w = self.if_sram_cfg_wst_s.wr_data
                for i in range(self._params.banks_per_tile):
                    self.ctrl2bank_m_wr_en_w[i] = 0
                    self.ctrl2bank_m_wr_addr_w[i] = 0
                    self.ctrl2bank_m_wr_data_w[i] = 0
        else:
            self.if_sram_cfg_est_m_wr_en_w = 0
            self.if_sram_cfg_est_m_wr_addr_w = 0
            self.if_sram_cfg_est_m_wr_data_w = 0
            for i in range(self._params.banks_per_tile):
                self.ctrl2bank_m_wr_en_w[i] = 0
                self.ctrl2bank_m_wr_addr_w[i] = 0
                self.ctrl2bank_m_wr_data_w[i] = 0

    @always_comb
    def rdrq_logic(self):
        self.rd_bank_sel = self.if_sram_cfg_wst_s.rd_addr[self.bank_sel_msb, self.bank_sel_lsb]
        if self.if_sram_cfg_wst_s.rd_en:
            if self.rd_tile_id_match:
                self.if_sram_cfg_est_m_rd_en_w = 0
                self.if_sram_cfg_est_m_rd_addr_w = 0
                for i in range(self._params.banks_per_tile):
                    if self.rd_bank_sel == i:
                        self.ctrl2bank_m_rd_en_w[i] = self.if_sram_cfg_wst_s.rd_en
                        self.ctrl2bank_m_rd_addr_w[i] = self.if_sram_cfg_wst_s.rd_addr[self._params.bank_addr_width - 1,
                                                                                       0]
                    else:
                        self.ctrl2bank_m_rd_en_w[i] = 0
                        self.ctrl2bank_m_rd_addr_w[i] = 0
            else:
                self.if_sram_cfg_est_m_rd_en_w = self.if_sram_cfg_wst_s.rd_en
                self.if_sram_cfg_est_m_rd_addr_w = self.if_sram_cfg_wst_s.rd_addr
                for i in range(self._params.banks_per_tile):
                    self.ctrl2bank_m_rd_en_w[i] = 0
                    self.ctrl2bank_m_rd_addr_w[i] = 0
        else:
            self.if_sram_cfg_est_m_rd_en_w = 0
            self.if_sram_cfg_est_m_rd_addr_w = 0
            for i in range(self._params.banks_per_tile):
                self.ctrl2bank_m_rd_en_w[i] = 0
                self.ctrl2bank_m_rd_addr_w[i] = 0

    @always_comb
    def rdrs_logic(self):
        self.rd_data_w = 0
        self.rd_data_valid_w = 0
        for i in range(self._params.banks_per_tile):
            if self.if_sram_cfg_ctrl2bank_m[i].rd_data_valid == 1:
                self.rd_data_w = self.if_sram_cfg_ctrl2bank_m[i].rd_data
                self.rd_data_valid_w = self.if_sram_cfg_ctrl2bank_m[i].rd_data_valid
        if self.if_sram_cfg_est_m.rd_data_valid == 1:
            self.rd_data_w = self.if_sram_cfg_est_m.rd_data
            self.rd_data_valid_w = self.if_sram_cfg_est_m.rd_data_valid

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def pipeline(self):
        if self.reset:
            self.if_sram_cfg_est_m.wr_en = 0
            self.if_sram_cfg_est_m.wr_addr = 0
            self.if_sram_cfg_est_m.wr_data = 0
            self.if_sram_cfg_est_m.rd_en = 0
            self.if_sram_cfg_est_m.rd_addr = 0
            self.if_sram_cfg_wst_s.rd_data = 0
            self.if_sram_cfg_wst_s.rd_data_valid = 0
            for i in range(self._params.banks_per_tile):
                self.if_sram_cfg_ctrl2bank_m[i].wr_en = 0
                self.if_sram_cfg_ctrl2bank_m[i].wr_addr = 0
                self.if_sram_cfg_ctrl2bank_m[i].wr_data = 0
                self.if_sram_cfg_ctrl2bank_m[i].rd_en = 0
                self.if_sram_cfg_ctrl2bank_m[i].rd_addr = 0
        else:
            self.if_sram_cfg_est_m.wr_en = self.if_sram_cfg_est_m_wr_en_w
            self.if_sram_cfg_est_m.wr_addr = self.if_sram_cfg_est_m_wr_addr_w
            self.if_sram_cfg_est_m.wr_data = self.if_sram_cfg_est_m_wr_data_w
            self.if_sram_cfg_est_m.rd_en = self.if_sram_cfg_est_m_rd_en_w
            self.if_sram_cfg_est_m.rd_addr = self.if_sram_cfg_est_m_rd_addr_w
            self.if_sram_cfg_wst_s.rd_data = self.rd_data_w
            self.if_sram_cfg_wst_s.rd_data_valid = self.rd_data_valid_w
            for i in range(self._params.banks_per_tile):
                self.if_sram_cfg_ctrl2bank_m[i].wr_en = self.ctrl2bank_m_wr_en_w[i]
                self.if_sram_cfg_ctrl2bank_m[i].wr_addr = self.ctrl2bank_m_wr_addr_w[i]
                self.if_sram_cfg_ctrl2bank_m[i].wr_data = self.ctrl2bank_m_wr_data_w[i]
                self.if_sram_cfg_ctrl2bank_m[i].rd_en = self.ctrl2bank_m_rd_en_w[i]
                self.if_sram_cfg_ctrl2bank_m[i].rd_addr = self.ctrl2bank_m_rd_addr_w[i]
