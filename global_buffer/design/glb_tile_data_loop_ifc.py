from kratos import Generator, Interface, clog2
import math


class GlbTileDataLoopInterface(Interface):
    def __init__(self, addr_width: int, data_width: int, is_clk_en=True, is_strb=False, has_wr_ifc=True, num_tracks=1, mu_word_num_tiles=4):
        self.addr_width = addr_width
        self.data_width = data_width
        self.is_clk_en = is_clk_en
        self.is_strb = is_strb
        self.has_wr_ifc = has_wr_ifc
        self.mu_word_num_tiles = mu_word_num_tiles
        self.num_tracks = num_tracks

        if not(self.has_wr_ifc):
            name = f"glb_tile_rd_only_data_loop_ifc_A_{addr_width}_{self.num_tracks}xD_{data_width}"
        else:
            name = f"glb_tile_data_loop_ifc_A_{addr_width}_{self.num_tracks}xD_{data_width}"
        Interface.__init__(self, name)

        # Local variables
        if self.has_wr_ifc:
            self.wr_en = self.var("wr_en", 1)
            if is_clk_en is True:
                self.wr_clk_en = self.var("wr_clk_en", 1)
            self.wr_addr = self.var("wr_addr", addr_width)
            self.wr_data = self.var("wr_data", data_width)
            if is_strb is True:
                self.wr_strb = self.var("wr_strb", math.ceil(data_width / 8))
        
        self.sub_packet_idx = self.var("sub_packet_idx", clog2(self.mu_word_num_tiles))
        self.rd_en = self.var("rd_en", 1)
        if is_clk_en is True:
            self.rd_clk_en = self.var("rd_clk_en", 1)
        self.rd_addr = self.var("rd_addr", addr_width)
        # self.rd_data_e2w = self.var("rd_data_e2w", data_width)
        # TODO: use this eventually
        self.rd_data_e2w = self.var("rd_data_e2w", self.data_width, self.num_tracks)
        self.rd_data_e2w_valid = self.var("rd_data_e2w_valid", 1, self.num_tracks)

        # self.rd_data_w2e = self.var("rd_data_w2e", data_width)
        # TODO: use this eventually
        self.rd_data_w2e = self.var("rd_data_w2e", self.data_width, self.num_tracks)
        self.rd_data_w2e_valid = self.var("rd_data_w2e_valid", 1, self.num_tracks)

        if self.has_wr_ifc:
            self.m_to_s = [self.wr_en, self.wr_addr, self.wr_data, self.rd_en, self.rd_addr, self.sub_packet_idx]
            if is_strb is True:
                self.m_to_s.append(self.wr_strb)
            if is_clk_en is True:
                self.m_to_s.extend([self.wr_clk_en, self.rd_clk_en])
        else:
            self.m_to_s = [self.rd_en, self.rd_addr, self.sub_packet_idx, self.rd_data_w2e, self.rd_data_w2e_valid]
            if is_clk_en is True:
                self.m_to_s.extend([self.rd_clk_en])

        self.s_to_m = [self.rd_data_e2w, self.rd_data_e2w_valid]
        self.ports = self.m_to_s + self.s_to_m

        self.master = self.modport("master")
        self.slave = self.modport("slave")

        for port in self.m_to_s:
            self.master.set_output(port)
            self.slave.set_input(port)
        for port in self.s_to_m:
            self.master.set_input(port)
            self.slave.set_output(port)
