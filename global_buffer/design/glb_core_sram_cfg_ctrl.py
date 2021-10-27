from kratos import Generator, always_ff, always_comb, posedge
from global_buffer.design.global_buffer_parameter import GlobalBufferParams
from global_buffer.design.glb_cfg_ifc import GlbConfigInterface
from global_buffer.design.glb_header import GlbHeader


class GlbCoreSramCfgCtrl(Generator):
    def __init__(self, _params: GlobalBufferParams):
        super().__init__("glb_core_sram_cfg_ctrl")
        self._params = _params
        self.header = GlbHeader(self._params)

        self.clk = self.clock("clk")
        self.reset = self.reset("reset")
        self.glb_tile_id = self.input(
            "glb_tile_id", self._params.tile_sel_addr_width)

        self.sram_cfg_ifc = GlbConfigInterface(
            addr_width=self._params.glb_addr_width, data_width=self._params.axi_data_width)

        self.bank_cfg_ifc = GlbConfigInterface(
            addr_width=self._params.bank_addr_width, data_width=self._params.axi_data_width)

        # config port
        self.if_sram_cfg_est_m = self.interface(
            self.sram_cfg_ifc.master, "if_sram_cfg_est_m", is_port=True)
        self.if_sram_cfg_wst_s = self.interface(
            self.sram_cfg_ifc.slave, "if_sram_cfg_wst_s", is_port=True)

        # bank_config port
        self.if_sram_cfg_core2bank_m = []
        for i in range(self._params.banks_per_tile):
            self.if_sram_cfg_core2bank_m.append(self.interface(
                self.bank_cfg_ifc.master, f"if_sram_cfg_core2bank_m_{i}", is_port=True))

        self.tile_id_match = self.var("tile_id_match", 1)

        self.bank2core_rd_data_valid_w = self.var(
            "bank2core_rd_data_valid_w", 1, size=self._params.banks_per_tile)
        self.bank2core_rd_data_w = self.var(
            "bank2core_rd_data_w", self._params.axi_data_width, size=self._params.banks_per_tile)
        self.rd_data_valid_w = self.var("rd_data_valid_w", 1)
        self.rd_data_w = self.var("rd_data_w", self._params.axi_data_width)

        self.add_always(self.tile_id_match_logic)
        for i in range(self._params.banks_per_tile):
            self.add_always(self.if_sram_cfg_core2bank_logic, i=i)
        self.add_always(self.rd_data_mux)
        self.add_always(self.sram_cfg_pipeline)

    @always_comb
    def tile_id_match_logic(self):
        self.tile_id_match = self.if_sram_cfg_wst_s.wr_addr[self._params.bank_addr_width + self._params.bank_sel_addr_width +
                                                            self._params.tile_sel_addr_width - 1, self._params.bank_addr_width + self._params.bank_sel_addr_width] == self.glb_tile_id

    @always_comb
    def if_sram_cfg_core2bank_logic(self, i):
        if self.tile_id_match:
            self.if_sram_cfg_core2bank_m[i].wr_en = ((self.if_sram_cfg_wst_s.wr_addr[self._params.bank_addr_width +
                                                   self._params.bank_sel_addr_width - 1, self._params.bank_addr_width] == i) & self.if_sram_cfg_wst_s.wr_en)
            self.if_sram_cfg_core2bank_m[i].wr_addr = self.if_sram_cfg_wst_s.wr_addr[self._params.bank_addr_width - 1, 0]
            self.if_sram_cfg_core2bank_m[i].wr_data = self.if_sram_cfg_wst_s.wr_data
            self.if_sram_cfg_core2bank_m[i].rd_en = ((self.if_sram_cfg_wst_s.rd_addr[self._params.bank_addr_width +
                                                   self._params.bank_sel_addr_width - 1, self._params.bank_addr_width] == i) & self.if_sram_cfg_wst_s.rd_en)
            self.if_sram_cfg_core2bank_m[i].rd_addr = self.if_sram_cfg_wst_s.rd_addr[self._params.bank_addr_width - 1, 0]
        else:
            self.if_sram_cfg_core2bank_m[i].wr_en = 0
            self.if_sram_cfg_core2bank_m[i].wr_addr = 0
            self.if_sram_cfg_core2bank_m[i].wr_data = 0
            self.if_sram_cfg_core2bank_m[i].rd_en = 0
            self.if_sram_cfg_core2bank_m[i].rd_addr = 0

    @always_comb
    def rd_data_mux(self):
        self.rd_data_w = self.if_sram_cfg_est_m.rd_data
        self.rd_data_valid_w = self.if_sram_cfg_est_m.rd_data_valid
        for i in range(self._params.banks_per_tile):
            if self.if_sram_cfg_core2bank_m[i].rd_data_valid == 1:
                self.rd_data_w = self.if_sram_cfg_core2bank_m[i].rd_data
                self.rd_data_valid_w = self.if_sram_cfg_core2bank_m[i].rd_data_valid

    @always_ff((posedge, "clk"), (posedge, "reset"))
    def sram_cfg_pipeline(self):
        if self.reset:
            self.if_sram_cfg_est_m.wr_en = 0
            self.if_sram_cfg_est_m.wr_addr = 0
            self.if_sram_cfg_est_m.wr_data = 0
            self.if_sram_cfg_est_m.rd_en = 0
            self.if_sram_cfg_est_m.rd_addr = 0
            self.if_sram_cfg_wst_s.rd_data = 0
            self.if_sram_cfg_wst_s.rd_data_valid = 0
        else:
            self.if_sram_cfg_est_m.wr_en = self.if_sram_cfg_wst_s.wr_en
            self.if_sram_cfg_est_m.wr_addr = self.if_sram_cfg_wst_s.wr_addr
            self.if_sram_cfg_est_m.wr_data = self.if_sram_cfg_wst_s.wr_data
            self.if_sram_cfg_est_m.rd_en = self.if_sram_cfg_wst_s.rd_en
            self.if_sram_cfg_est_m.rd_addr = self.if_sram_cfg_wst_s.rd_addr
            self.if_sram_cfg_wst_s.rd_data = self.rd_data_w
            self.if_sram_cfg_wst_s.rd_data_valid = self.rd_data_valid_w
