from kratos import Generator, RawStringStmt
from global_buffer.design.glb_core import GlbCore
from global_buffer.design.glb_tile_cfg import GlbTileCfg
from global_buffer.design.glb_tile_pcfg_switch import GlbTilePcfgSwitch
from global_buffer.design.glb_tile_sram_cfg_ctrl import GlbTileSramCfgCtrl
from global_buffer.design.glb_cfg_ifc import GlbConfigInterface
from global_buffer.design.global_buffer_parameter import GlobalBufferParams
from global_buffer.design.glb_header import GlbHeader
from global_buffer.design.glb_bank import GlbBank


class GlbTile(Generator):
    def __init__(self, _params: GlobalBufferParams):
        super().__init__("glb_tile")
        self._params = _params
        self.header = GlbHeader(self._params)

        self.clk = self.clock("clk")
        self.clk_en = self.clock_en("clk_en")
        self.reset = self.reset("reset")
        self.glb_tile_id = self.input("glb_tile_id", self._params.tile_sel_addr_width)

        self.proc_w2e_wsti_dict = {}
        for port, size in self.header.packet_ports:
            name = f"proc_{port}_w2e_wsti"
            self.proc_w2e_wsti_dict[port] = self.input(name, size)

        self.proc_w2e_esto_dict = {}
        for port, size in self.header.packet_ports:
            name = f"proc_{port}_w2e_esto"
            self.proc_w2e_esto_dict[port] = self.output(name, size)

        self.proc_e2w_esti_dict = {}
        for port, size in self.header.rdrs_packet_ports:
            name = f"proc_{port}_e2w_esti"
            self.proc_e2w_esti_dict[port] = self.input(name, size)

        self.proc_e2w_wsto_dict = {}
        for port, size in self.header.rdrs_packet_ports:
            name = f"proc_{port}_e2w_wsto"
            self.proc_e2w_wsto_dict[port] = self.output(name, size)

        self.strm_w2e_wsti_dict = {}
        for port, size in self.header.packet_ports:
            name = f"strm_{port}_w2e_wsti"
            self.strm_w2e_wsti_dict[port] = self.input(name, size)

        self.strm_w2e_esto_dict = {}
        for port, size in self.header.packet_ports:
            name = f"strm_{port}_w2e_esto"
            self.strm_w2e_esto_dict[port] = self.output(name, size)

        self.strm_e2w_esti_dict = {}
        for port, size in self.header.packet_ports:
            name = f"strm_{port}_e2w_esti"
            self.strm_e2w_esti_dict[port] = self.input(name, size)

        self.strm_e2w_wsto_dict = {}
        for port, size in self.header.packet_ports:
            name = f"strm_{port}_e2w_wsto"
            self.strm_e2w_wsto_dict[port] = self.output(name, size)

        self.pcfg_w2e_wsti_dict = {}
        for port, size in self.header.rd_packet_ports:
            name = f"pcfg_{port}_w2e_wsti"
            self.pcfg_w2e_wsti_dict[port] = self.input(name, size)

        self.pcfg_w2e_esto_dict = {}
        for port, size in self.header.rd_packet_ports:
            name = f"pcfg_{port}_w2e_esto"
            self.pcfg_w2e_esto_dict[port] = self.output(name, size)

        self.pcfg_e2w_esti_dict = {}
        for port, size in self.header.rd_packet_ports:
            name = f"pcfg_{port}_e2w_esti"
            self.pcfg_e2w_esti_dict[port] = self.input(name, size)

        self.pcfg_e2w_wsto_dict = {}
        for port, size in self.header.rd_packet_ports:
            name = f"pcfg_{port}_e2w_wsto"
            self.pcfg_e2w_wsto_dict[port] = self.output(name, size)

        self.if_cfg_est_m_wr_en = self.output("if_cfg_est_m_wr_en", 1)
        self.if_cfg_est_m_wr_addr = self.output("if_cfg_est_m_wr_addr", self._params.axi_addr_width)
        self.if_cfg_est_m_wr_data = self.output("if_cfg_est_m_wr_data", self._params.axi_data_width)
        self.if_cfg_est_m_rd_en = self.output("if_cfg_est_m_rd_en", 1)
        self.if_cfg_est_m_rd_addr = self.output("if_cfg_est_m_rd_addr", self._params.axi_addr_width)
        self.if_cfg_est_m_rd_data = self.input("if_cfg_est_m_rd_data", self._params.axi_data_width)
        self.if_cfg_est_m_rd_data_valid = self.input("if_cfg_est_m_rd_data_valid", 1)

        self.if_cfg_wst_s_wr_en = self.input("if_cfg_wst_s_wr_en", 1)
        self.if_cfg_wst_s_wr_addr = self.input("if_cfg_wst_s_wr_addr", self._params.axi_addr_width)
        self.if_cfg_wst_s_wr_data = self.input("if_cfg_wst_s_wr_data", self._params.axi_data_width)
        self.if_cfg_wst_s_rd_en = self.input("if_cfg_wst_s_rd_en", 1)
        self.if_cfg_wst_s_rd_addr = self.input("if_cfg_wst_s_rd_addr", self._params.axi_addr_width)
        self.if_cfg_wst_s_rd_data = self.output("if_cfg_wst_s_rd_data", self._params.axi_data_width)
        self.if_cfg_wst_s_rd_data_valid = self.output("if_cfg_wst_s_rd_data_valid", 1)

        self.if_sram_cfg_est_m_wr_en = self.output("if_sram_cfg_est_m_wr_en", 1)
        self.if_sram_cfg_est_m_wr_addr = self.output("if_sram_cfg_est_m_wr_addr", self._params.glb_addr_width)
        self.if_sram_cfg_est_m_wr_data = self.output("if_sram_cfg_est_m_wr_data", self._params.axi_data_width)
        self.if_sram_cfg_est_m_rd_en = self.output("if_sram_cfg_est_m_rd_en", 1)
        self.if_sram_cfg_est_m_rd_addr = self.output("if_sram_cfg_est_m_rd_addr", self._params.glb_addr_width)
        self.if_sram_cfg_est_m_rd_data = self.input("if_sram_cfg_est_m_rd_data", self._params.axi_data_width)
        self.if_sram_cfg_est_m_rd_data_valid = self.input("if_sram_cfg_est_m_rd_data_valid", 1)

        self.if_sram_cfg_wst_s_wr_en = self.input("if_sram_cfg_wst_s_wr_en", 1)
        self.if_sram_cfg_wst_s_wr_addr = self.input("if_sram_cfg_wst_s_wr_addr", self._params.glb_addr_width)
        self.if_sram_cfg_wst_s_wr_data = self.input("if_sram_cfg_wst_s_wr_data", self._params.axi_data_width)
        self.if_sram_cfg_wst_s_rd_en = self.input("if_sram_cfg_wst_s_rd_en", 1)
        self.if_sram_cfg_wst_s_rd_addr = self.input("if_sram_cfg_wst_s_rd_addr", self._params.glb_addr_width)
        self.if_sram_cfg_wst_s_rd_data = self.output("if_sram_cfg_wst_s_rd_data", self._params.axi_data_width)
        self.if_sram_cfg_wst_s_rd_data_valid = self.output("if_sram_cfg_wst_s_rd_data_valid", 1)

        self.cfg_tile_connected_wsti = self.input("cfg_tile_connected_wsti", 1)
        self.cfg_tile_connected_esto = self.output("cfg_tile_connected_esto", 1)
        self.cfg_pcfg_tile_connected_wsti = self.input("cfg_pcfg_tile_connected_wsti", 1)
        self.cfg_pcfg_tile_connected_esto = self.output("cfg_pcfg_tile_connected_esto", 1)

        self.cgra_cfg_jtag_wsti_wr_en = self.input("cgra_cfg_jtag_wsti_wr_en", 1)
        self.cgra_cfg_jtag_wsti_rd_en = self.input("cgra_cfg_jtag_wsti_rd_en", 1)
        self.cgra_cfg_jtag_wsti_addr = self.input("cgra_cfg_jtag_wsti_addr", self._params.cgra_cfg_addr_width)
        self.cgra_cfg_jtag_wsti_data = self.input("cgra_cfg_jtag_wsti_data", self._params.cgra_cfg_data_width)

        self.cgra_cfg_jtag_esto_wr_en = self.output("cgra_cfg_jtag_esto_wr_en", 1)
        self.cgra_cfg_jtag_esto_rd_en = self.output("cgra_cfg_jtag_esto_rd_en", 1)
        self.cgra_cfg_jtag_esto_addr = self.output("cgra_cfg_jtag_esto_addr", self._params.cgra_cfg_addr_width)
        self.cgra_cfg_jtag_esto_data = self.output("cgra_cfg_jtag_esto_data", self._params.cgra_cfg_data_width)

        self.cgra_cfg_jtag_wsti_rd_en_bypass = self.input("cgra_cfg_jtag_wsti_rd_en_bypass", 1)
        self.cgra_cfg_jtag_wsti_addr_bypass = self.input(
            "cgra_cfg_jtag_wsti_addr_bypass", self._params.cgra_cfg_addr_width)
        self.cgra_cfg_jtag_esto_rd_en_bypass = self.output("cgra_cfg_jtag_esto_rd_en_bypass", 1)
        self.cgra_cfg_jtag_esto_addr_bypass = self.output(
            "cgra_cfg_jtag_esto_addr_bypass", self._params.cgra_cfg_addr_width)

        self.cgra_cfg_pcfg_wsti_wr_en = self.input("cgra_cfg_pcfg_wsti_wr_en", 1)
        self.cgra_cfg_pcfg_wsti_rd_en = self.input("cgra_cfg_pcfg_wsti_rd_en", 1)
        self.cgra_cfg_pcfg_wsti_addr = self.input("cgra_cfg_pcfg_wsti_addr", self._params.cgra_cfg_addr_width)
        self.cgra_cfg_pcfg_wsti_data = self.input("cgra_cfg_pcfg_wsti_data", self._params.cgra_cfg_data_width)

        self.cgra_cfg_pcfg_esto_wr_en = self.output("cgra_cfg_pcfg_esto_wr_en", 1)
        self.cgra_cfg_pcfg_esto_rd_en = self.output("cgra_cfg_pcfg_esto_rd_en", 1)
        self.cgra_cfg_pcfg_esto_addr = self.output("cgra_cfg_pcfg_esto_addr", self._params.cgra_cfg_addr_width)
        self.cgra_cfg_pcfg_esto_data = self.output("cgra_cfg_pcfg_esto_data", self._params.cgra_cfg_data_width)

        self.stream_data_f2g = self.input("stream_data_f2g", self._params.cgra_data_width,
                                          size=self._params.cgra_per_glb, packed=True)
        self.stream_data_valid_f2g = self.input("stream_data_valid_f2g", 1, size=self._params.cgra_per_glb, packed=True)
        self.stream_data_g2f = self.output("stream_data_g2f", self._params.cgra_data_width,
                                           size=self._params.cgra_per_glb, packed=True)
        self.stream_data_valid_g2f = self.output(
            "stream_data_valid_g2f", 1, size=self._params.cgra_per_glb, packed=True)

        self.cgra_cfg_g2f_cfg_wr_en = self.output(
            "cgra_cfg_g2f_cfg_wr_en", 1, size=self._params.cgra_per_glb, packed=True)
        self.cgra_cfg_g2f_cfg_rd_en = self.output(
            "cgra_cfg_g2f_cfg_rd_en", 1, size=self._params.cgra_per_glb, packed=True)
        self.cgra_cfg_g2f_cfg_addr = self.output(
            "cgra_cfg_g2f_cfg_addr", self._params.cgra_cfg_addr_width, size=self._params.cgra_per_glb, packed=True)
        self.cgra_cfg_g2f_cfg_data = self.output(
            "cgra_cfg_g2f_cfg_data", self._params.cgra_cfg_data_width, size=self._params.cgra_per_glb, packed=True)

        self.strm_g2f_start_pulse = self.input("strm_g2f_start_pulse", 1)
        self.strm_f2g_start_pulse = self.input("strm_f2g_start_pulse", 1)
        self.pcfg_start_pulse = self.input("pcfg_start_pulse", 1)
        self.strm_f2g_interrupt_pulse = self.output("strm_f2g_interrupt_pulse", 1)
        self.strm_g2f_interrupt_pulse = self.output("strm_g2f_interrupt_pulse", 1)
        self.pcfg_g2f_interrupt_pulse = self.output("pcfg_g2f_interrupt_pulse", 1)

        self.if_cfg = GlbConfigInterface(addr_width=self._params.axi_addr_width, data_width=self._params.axi_data_width)
        self.if_sram_cfg = GlbConfigInterface(addr_width=self._params.glb_addr_width,
                                              data_width=self._params.axi_data_width)

        self.if_cfg_est_m = self.interface(self.if_cfg, "if_cfg_est_m")
        self.if_cfg_wst_s = self.interface(self.if_cfg, "if_cfg_wst_s")
        self.if_sram_cfg_est_m = self.interface(self.if_sram_cfg, "if_sram_cfg_est_m")
        self.if_sram_cfg_wst_s = self.interface(self.if_sram_cfg, "if_sram_cfg_wst_s")

        self.wr_packet_sw2bankarr = self.var(
            "wr_packet_sw2bankarr", self.header.wr_packet_t, size=self._params.banks_per_tile)
        self.rdrq_packet_sw2bankarr = self.var(
            "rdrq_packet_sw2bankarr", self.header.rdrq_packet_t, size=self._params.banks_per_tile)
        self.rdrs_packet_bankarr2sw = self.var(
            "rdrs_packet_bankarr2sw", self.header.rdrs_packet_t, size=self._params.banks_per_tile)

        self.glb_tile_cfg = GlbTileCfg(_params=self._params)
        self.add_child("glb_tile_cfg",
                       self.glb_tile_cfg,
                       clk=self.clk,
                       reset=self.reset,
                       glb_tile_id=self.glb_tile_id)

        self.glb_tile_pcfg_switch = GlbTilePcfgSwitch(_params=self._params)
        self.add_child("glb_tile_pcfg_switch",
                       self.glb_tile_pcfg_switch,
                       clk=self.clk,
                       reset=self.reset)

        self.glb_core = GlbCore(_params=self._params)
        self.add_child("glb_core",
                       self.glb_core,
                       clk=self.clk,
                       clk_en=self.clk_en,
                       reset=self.reset,
                       glb_tile_id=self.glb_tile_id,
                       wr_packet_sw2bankarr=self.wr_packet_sw2bankarr,
                       rdrq_packet_sw2bankarr=self.rdrq_packet_sw2bankarr,
                       rdrs_packet_bankarr2sw=self.rdrs_packet_bankarr2sw
                       )

        self.if_sram_cfg_bank2ctrl = []
        for i in range(self._params.banks_per_tile):
            if_sram_cfg_bank2ctrl = self.interface(GlbConfigInterface(addr_width=self._params.bank_addr_width,
                                                                      data_width=self._params.axi_data_width),
                                                   f"if_sram_cfg_bank2core_{i}")
            self.if_sram_cfg_bank2ctrl.append(if_sram_cfg_bank2ctrl)

        self.glb_tile_sram_cfg_ctrl = GlbTileSramCfgCtrl(self._params)
        self.add_child("glb_tile_sram_cfg_ctrl",
                       self.glb_tile_sram_cfg_ctrl,
                       clk=self.clk,
                       reset=self.reset,
                       glb_tile_id=self.glb_tile_id,
                       if_sram_cfg_est_m=self.if_sram_cfg_est_m,
                       if_sram_cfg_wst_s=self.if_sram_cfg_wst_s)
        for i in range(self._params.banks_per_tile):
            self.wire(self.glb_tile_sram_cfg_ctrl.if_sram_cfg_ctrl2bank_m[i], self.if_sram_cfg_bank2ctrl[i])

        self.glb_bank_arr = []
        for i in range(self._params.banks_per_tile):
            glb_bank = GlbBank(self._params)
            self.add_child(f"glb_bank_{i}",
                           glb_bank,
                           clk=self.clk,
                           reset=self.reset,
                           wr_packet=self.wr_packet_sw2bankarr[i],
                           rdrq_packet=self.rdrq_packet_sw2bankarr[i],
                           rdrs_packet=self.rdrs_packet_bankarr2sw[i],
                           if_sram_cfg_s=self.if_sram_cfg_bank2ctrl[i])
            self.glb_bank_arr.append(glb_bank)

        if self._params.is_sram_stub:
            self.readmemh_block = RawStringStmt(["initial begin",
                                                "\tstring b0_file_name;",
                                                "\tstring b1_file_name;",
                                                "\tstring load_arg;",
                                                "\t$sformat(b0_file_name, \"testvectors/tile%0d_b0.dat\", glb_tile_id);",  # noqa
                                                "\t$sformat(b1_file_name, \"testvectors/tile%0d_b1.dat\", glb_tile_id);",  # noqa
                                                "\t$sformat(load_arg, \"LOAD%0d\", glb_tile_id);",
                                                "\tif (($test$plusargs(load_arg))) begin",
                                                "\t\t$readmemh(b0_file_name, glb_core.glb_bank_0.glb_bank_memory.glb_bank_sram_stub.mem);",  # noqa
                                                "\t\t$readmemh(b1_file_name, glb_core.glb_bank_1.glb_bank_memory.glb_bank_sram_stub.mem);",  # noqa
                                                "\tend",
                                                "end"])
            self.writememh_block = RawStringStmt(["final begin",
                                                "\tstring b0_file_name;",
                                                "\tstring b1_file_name;",
                                                "\tstring save_arg;",
                                                "\t$sformat(b0_file_name, \"testvectors/tile%0d_b0_out.dat\", glb_tile_id);",  # noqa
                                                "\t$sformat(b1_file_name, \"testvectors/tile%0d_b1_out.dat\", glb_tile_id);",  # noqa
                                                "\t$sformat(save_arg, \"SAVE%0d\", glb_tile_id);",
                                                "\tif (($test$plusargs(save_arg))) begin",
                                                "\t\t$writememh(b0_file_name, glb_core.glb_bank_0.glb_bank_memory.glb_bank_sram_stub.mem);",  # noqa
                                                "\t\t$writememh(b1_file_name, glb_core.glb_bank_1.glb_bank_memory.glb_bank_sram_stub.mem);",  # noqa
                                                "\tend",
                                                "end"])
            self.add_stmt(self.readmemh_block.stmt())
            self.add_stmt(self.writememh_block.stmt())

        self.interface_wiring()
        self.tile2cfg_wiring()
        self.tile2core_wiring()
        self.tile2pcfgs_wiring()
        self.cfg2core_wiring()
        self.core2pcfgs_wiring()

    def interface_wiring(self):
        self.wire(self.if_cfg_est_m.wr_en, self.if_cfg_est_m_wr_en)
        self.wire(self.if_cfg_est_m.wr_addr, self.if_cfg_est_m_wr_addr)
        self.wire(self.if_cfg_est_m.wr_data, self.if_cfg_est_m_wr_data)
        self.wire(self.if_cfg_est_m.rd_en, self.if_cfg_est_m_rd_en)
        self.wire(self.if_cfg_est_m.rd_addr, self.if_cfg_est_m_rd_addr)
        self.wire(self.if_cfg_est_m.rd_data, self.if_cfg_est_m_rd_data)
        self.wire(self.if_cfg_est_m.rd_data_valid, self.if_cfg_est_m_rd_data_valid)

        self.wire(self.if_cfg_wst_s.wr_en, self.if_cfg_wst_s_wr_en)
        self.wire(self.if_cfg_wst_s.wr_addr, self.if_cfg_wst_s_wr_addr)
        self.wire(self.if_cfg_wst_s.wr_data, self.if_cfg_wst_s_wr_data)
        self.wire(self.if_cfg_wst_s.rd_en, self.if_cfg_wst_s_rd_en)
        self.wire(self.if_cfg_wst_s.rd_addr, self.if_cfg_wst_s_rd_addr)
        self.wire(self.if_cfg_wst_s.rd_data, self.if_cfg_wst_s_rd_data)
        self.wire(self.if_cfg_wst_s.rd_data_valid, self.if_cfg_wst_s_rd_data_valid)

        self.wire(self.if_sram_cfg_est_m.wr_en, self.if_sram_cfg_est_m_wr_en)
        self.wire(self.if_sram_cfg_est_m.wr_addr, self.if_sram_cfg_est_m_wr_addr)
        self.wire(self.if_sram_cfg_est_m.wr_data, self.if_sram_cfg_est_m_wr_data)
        self.wire(self.if_sram_cfg_est_m.rd_en, self.if_sram_cfg_est_m_rd_en)
        self.wire(self.if_sram_cfg_est_m.rd_addr, self.if_sram_cfg_est_m_rd_addr)
        self.wire(self.if_sram_cfg_est_m.rd_data, self.if_sram_cfg_est_m_rd_data)
        self.wire(self.if_sram_cfg_est_m.rd_data_valid, self.if_sram_cfg_est_m_rd_data_valid)

        self.wire(self.if_sram_cfg_wst_s.wr_en, self.if_sram_cfg_wst_s_wr_en)
        self.wire(self.if_sram_cfg_wst_s.wr_addr, self.if_sram_cfg_wst_s_wr_addr)
        self.wire(self.if_sram_cfg_wst_s.wr_data, self.if_sram_cfg_wst_s_wr_data)
        self.wire(self.if_sram_cfg_wst_s.rd_en, self.if_sram_cfg_wst_s_rd_en)
        self.wire(self.if_sram_cfg_wst_s.rd_addr, self.if_sram_cfg_wst_s_rd_addr)
        self.wire(self.if_sram_cfg_wst_s.rd_data, self.if_sram_cfg_wst_s_rd_data)
        self.wire(self.if_sram_cfg_wst_s.rd_data_valid, self.if_sram_cfg_wst_s_rd_data_valid)

    def tile2cfg_wiring(self):
        self.wire(self.glb_tile_cfg.if_cfg_wst_s, self.if_cfg_wst_s)
        self.wire(self.glb_tile_cfg.if_cfg_est_m, self.if_cfg_est_m)

    def tile2core_wiring(self):
        for port, _ in self.header.wr_packet_ports:
            self.wire(self.glb_core.proc_wr_packet_w2e_wsti[port], self.proc_w2e_wsti_dict[port])
        for port, _ in self.header.wr_packet_ports:
            self.wire(self.glb_core.proc_wr_packet_w2e_esto[port], self.proc_w2e_esto_dict[port])

        for port, _ in self.header.rdrq_packet_ports:
            self.wire(self.glb_core.proc_rdrq_packet_w2e_wsti[port], self.proc_w2e_wsti_dict[port])
        for port, _ in self.header.rdrq_packet_ports:
            self.wire(self.glb_core.proc_rdrq_packet_w2e_esto[port], self.proc_w2e_esto_dict[port])

        for port, _ in self.header.rdrs_packet_ports:
            self.wire(self.glb_core.proc_rdrs_packet_e2w_wsto[port], self.proc_e2w_wsto_dict[port])
        for port, _ in self.header.rdrs_packet_ports:
            self.wire(self.glb_core.proc_rdrs_packet_e2w_esti[port], self.proc_e2w_esti_dict[port])
        for port, _ in self.header.rdrs_packet_ports:
            self.wire(self.glb_core.proc_rdrs_packet_w2e_wsti[port], self.proc_w2e_wsti_dict[port])
        for port, _ in self.header.rdrs_packet_ports:
            self.wire(self.glb_core.proc_rdrs_packet_w2e_esto[port], self.proc_w2e_esto_dict[port])

        for port, _ in self.header.wr_packet_ports:
            self.wire(self.glb_core.strm_wr_packet_w2e_wsti[port], self.strm_w2e_wsti_dict[port])
        for port, _ in self.header.wr_packet_ports:
            self.wire(self.glb_core.strm_wr_packet_w2e_esto[port], self.strm_w2e_esto_dict[port])
        for port, _ in self.header.wr_packet_ports:
            self.wire(self.glb_core.strm_wr_packet_e2w_esti[port], self.strm_e2w_esti_dict[port])
        for port, _ in self.header.wr_packet_ports:
            self.wire(self.glb_core.strm_wr_packet_e2w_wsto[port], self.strm_e2w_wsto_dict[port])

        for port, _ in self.header.rdrq_packet_ports:
            self.wire(self.glb_core.strm_rdrq_packet_w2e_wsti[port], self.strm_w2e_wsti_dict[port])
        for port, _ in self.header.rdrq_packet_ports:
            self.wire(self.glb_core.strm_rdrq_packet_w2e_esto[port], self.strm_w2e_esto_dict[port])
        for port, _ in self.header.rdrq_packet_ports:
            self.wire(self.glb_core.strm_rdrq_packet_e2w_esti[port], self.strm_e2w_esti_dict[port])
        for port, _ in self.header.rdrq_packet_ports:
            self.wire(self.glb_core.strm_rdrq_packet_e2w_wsto[port], self.strm_e2w_wsto_dict[port])

        for port, _ in self.header.rdrs_packet_ports:
            self.wire(self.glb_core.strm_rdrs_packet_e2w_wsto[port], self.strm_e2w_wsto_dict[port])
        for port, _ in self.header.rdrs_packet_ports:
            self.wire(self.glb_core.strm_rdrs_packet_e2w_esti[port], self.strm_e2w_esti_dict[port])
        for port, _ in self.header.rdrs_packet_ports:
            self.wire(self.glb_core.strm_rdrs_packet_w2e_wsti[port], self.strm_w2e_wsti_dict[port])
        for port, _ in self.header.rdrs_packet_ports:
            self.wire(self.glb_core.strm_rdrs_packet_w2e_esto[port], self.strm_w2e_esto_dict[port])

        for port, _ in self.header.rdrq_packet_ports:
            self.wire(self.glb_core.pcfg_rdrq_packet_w2e_wsti[port], self.pcfg_w2e_wsti_dict[port])
        for port, _ in self.header.rdrq_packet_ports:
            self.wire(self.glb_core.pcfg_rdrq_packet_w2e_esto[port], self.pcfg_w2e_esto_dict[port])
        for port, _ in self.header.rdrq_packet_ports:
            self.wire(self.glb_core.pcfg_rdrq_packet_e2w_esti[port], self.pcfg_e2w_esti_dict[port])
        for port, _ in self.header.rdrq_packet_ports:
            self.wire(self.glb_core.pcfg_rdrq_packet_e2w_wsto[port], self.pcfg_e2w_wsto_dict[port])

        for port, _ in self.header.rdrs_packet_ports:
            self.wire(self.glb_core.pcfg_rdrs_packet_e2w_wsto[port], self.pcfg_e2w_wsto_dict[port])
        for port, _ in self.header.rdrs_packet_ports:
            self.wire(self.glb_core.pcfg_rdrs_packet_e2w_esti[port], self.pcfg_e2w_esti_dict[port])
        for port, _ in self.header.rdrs_packet_ports:
            self.wire(self.glb_core.pcfg_rdrs_packet_w2e_wsti[port], self.pcfg_w2e_wsti_dict[port])
        for port, _ in self.header.rdrs_packet_ports:
            self.wire(self.glb_core.pcfg_rdrs_packet_w2e_esto[port], self.pcfg_w2e_esto_dict[port])

        self.wire(self.glb_core.strm_data_valid_f2g, self.stream_data_valid_f2g)
        self.wire(self.glb_core.strm_data_valid_g2f, self.stream_data_valid_g2f)
        self.wire(self.glb_core.strm_data_f2g, self.stream_data_f2g)
        self.wire(self.glb_core.strm_data_g2f, self.stream_data_g2f)

        self.wire(self.cfg_tile_connected_esto, self.glb_tile_cfg.cfg_data_network['tile_connected'])
        self.wire(self.cfg_pcfg_tile_connected_esto, self.glb_tile_cfg.cfg_pcfg_network['tile_connected'])
        self.wire(self.glb_core.cfg_data_network_connected_prev, self.cfg_tile_connected_wsti)
        self.wire(self.glb_core.cfg_pcfg_network_connected_prev, self.cfg_pcfg_tile_connected_wsti)

        self.wire(self.glb_core.ld_dma_start_pulse, self.strm_g2f_start_pulse)
        self.wire(self.glb_core.st_dma_start_pulse, self.strm_f2g_start_pulse)
        self.wire(self.glb_core.pcfg_start_pulse, self.pcfg_start_pulse)
        self.wire(self.glb_core.ld_dma_done_pulse, self.strm_g2f_interrupt_pulse)
        self.wire(self.glb_core.st_dma_done_pulse, self.strm_f2g_interrupt_pulse)
        self.wire(self.glb_core.pcfg_done_pulse, self.pcfg_g2f_interrupt_pulse)

    def cfg2core_wiring(self):
        self.wire(self.glb_core.cfg_data_network, self.glb_tile_cfg.cfg_data_network)
        self.wire(self.glb_core.cfg_pcfg_network, self.glb_tile_cfg.cfg_pcfg_network)

        self.wire(self.glb_core.cfg_st_dma_ctrl, self.glb_tile_cfg.cfg_st_dma_ctrl)
        # NOTE: Kratos bug - Cannot directly wire struct array from two different modules
        st_dma_header_w = self.var("st_dma_header_w", self.header.cfg_dma_header_t, size=self._params.queue_depth)
        self.wire(st_dma_header_w, self.glb_tile_cfg.cfg_st_dma_header)
        self.wire(self.glb_core.cfg_st_dma_header, st_dma_header_w)

        self.wire(self.glb_core.cfg_ld_dma_ctrl, self.glb_tile_cfg.cfg_ld_dma_ctrl)
        ld_dma_header_w = self.var("ld_dma_header_w", self.header.cfg_dma_header_t, size=self._params.queue_depth)
        self.wire(self.glb_core.cfg_ld_dma_header, ld_dma_header_w)
        self.wire(ld_dma_header_w, self.glb_tile_cfg.cfg_ld_dma_header)

        self.wire(self.glb_core.cfg_pcfg_dma_ctrl, self.glb_tile_cfg.cfg_pcfg_dma_ctrl)
        self.wire(self.glb_core.cfg_pcfg_dma_header, self.glb_tile_cfg.cfg_pcfg_dma_header)

    def core2pcfgs_wiring(self):
        self.wire(self.glb_core.cgra_cfg_pcfg, self.glb_tile_pcfg_switch.cgra_cfg_core2sw)
        self.wire(self.glb_tile_cfg.cfg_pcfg_dma_ctrl['mode'], self.glb_tile_pcfg_switch.cfg_pcfg_dma_mode)

    def tile2pcfgs_wiring(self):
        cgra_cfg_g2f_w = self.var(f"cgra_cfg_g2f_cfg_w", self.header.cgra_cfg_t,
                                  size=self._params.cgra_per_glb, packed=True)
        self.wire(self.glb_tile_pcfg_switch.cgra_cfg_g2f, cgra_cfg_g2f_w)
        for i in range(self._params.cgra_per_glb):
            self.wire(cgra_cfg_g2f_w[i]['wr_en'], self.cgra_cfg_g2f_cfg_wr_en[i])
            self.wire(cgra_cfg_g2f_w[i]['rd_en'], self.cgra_cfg_g2f_cfg_rd_en[i])
            self.wire(cgra_cfg_g2f_w[i]['addr'], self.cgra_cfg_g2f_cfg_addr[i])
            self.wire(cgra_cfg_g2f_w[i]['data'], self.cgra_cfg_g2f_cfg_data[i])

        self.wire(self.glb_tile_pcfg_switch.cgra_cfg_jtag_wsti['wr_en'], self.cgra_cfg_jtag_wsti_wr_en)
        self.wire(self.glb_tile_pcfg_switch.cgra_cfg_jtag_wsti['rd_en'], self.cgra_cfg_jtag_wsti_rd_en)
        self.wire(self.glb_tile_pcfg_switch.cgra_cfg_jtag_wsti['addr'], self.cgra_cfg_jtag_wsti_addr)
        self.wire(self.glb_tile_pcfg_switch.cgra_cfg_jtag_wsti['data'], self.cgra_cfg_jtag_wsti_data)
        self.wire(self.glb_tile_pcfg_switch.cgra_cfg_jtag_esto['wr_en'], self.cgra_cfg_jtag_esto_wr_en)
        self.wire(self.glb_tile_pcfg_switch.cgra_cfg_jtag_esto['rd_en'], self.cgra_cfg_jtag_esto_rd_en)
        self.wire(self.glb_tile_pcfg_switch.cgra_cfg_jtag_esto['addr'], self.cgra_cfg_jtag_esto_addr)
        self.wire(self.glb_tile_pcfg_switch.cgra_cfg_jtag_esto['data'], self.cgra_cfg_jtag_esto_data)

        self.wire(self.glb_tile_pcfg_switch.cgra_cfg_pcfg_wsti['wr_en'], self.cgra_cfg_pcfg_wsti_wr_en)
        self.wire(self.glb_tile_pcfg_switch.cgra_cfg_pcfg_wsti['rd_en'], self.cgra_cfg_pcfg_wsti_rd_en)
        self.wire(self.glb_tile_pcfg_switch.cgra_cfg_pcfg_wsti['addr'], self.cgra_cfg_pcfg_wsti_addr)
        self.wire(self.glb_tile_pcfg_switch.cgra_cfg_pcfg_wsti['data'], self.cgra_cfg_pcfg_wsti_data)
        self.wire(self.glb_tile_pcfg_switch.cgra_cfg_pcfg_esto['wr_en'], self.cgra_cfg_pcfg_esto_wr_en)
        self.wire(self.glb_tile_pcfg_switch.cgra_cfg_pcfg_esto['rd_en'], self.cgra_cfg_pcfg_esto_rd_en)
        self.wire(self.glb_tile_pcfg_switch.cgra_cfg_pcfg_esto['addr'], self.cgra_cfg_pcfg_esto_addr)
        self.wire(self.glb_tile_pcfg_switch.cgra_cfg_pcfg_esto['data'], self.cgra_cfg_pcfg_esto_data)

        self.wire(self.glb_tile_pcfg_switch.cgra_cfg_jtag_wsti_rd_en_bypass, self.cgra_cfg_jtag_wsti_rd_en_bypass)
        self.wire(self.glb_tile_pcfg_switch.cgra_cfg_jtag_esto_rd_en_bypass, self.cgra_cfg_jtag_esto_rd_en_bypass)
        self.wire(self.glb_tile_pcfg_switch.cgra_cfg_jtag_wsti_addr_bypass, self.cgra_cfg_jtag_wsti_addr_bypass)
        self.wire(self.glb_tile_pcfg_switch.cgra_cfg_jtag_esto_addr_bypass, self.cgra_cfg_jtag_esto_addr_bypass)
