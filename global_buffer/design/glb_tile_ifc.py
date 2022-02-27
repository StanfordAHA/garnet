from kratos import Interface
import math


class GlbTileInterface(Interface):
    def __init__(self, addr_width: int, data_width: int, is_clk_en=True, is_strb=False):
        Interface.__init__(self, f"glb_tile_ifc_A_{addr_width}_D_{data_width}")
        self.addr_width = addr_width
        self.data_width = data_width
        self.is_clk_en = is_clk_en
        self.is_strb = is_strb

        # Local variables
        self.wr_en = self.var("wr_en", 1)
        if is_clk_en is True:
            self.wr_clk_en = self.var("wr_clk_en", 1)
        self.wr_addr = self.var("wr_addr", addr_width)
        self.wr_data = self.var("wr_data", data_width)
        if is_strb is True:
            self.wr_strb = self.var("wr_strb", math.ceil(data_width / 8))
        self.rd_en = self.var("rd_en", 1)
        if is_clk_en is True:
            self.rd_clk_en = self.var("rd_clk_en", 1)
        self.rd_addr = self.var("rd_addr", addr_width)
        self.rd_data = self.var("rd_data", data_width)
        self.rd_data_valid = self.var("rd_data_valid", 1)

        self.m_to_s = [self.wr_en, self.wr_addr, self.wr_data, self.rd_en, self.rd_addr]
        if is_strb is True:
            self.m_to_s.append(self.wr_strb)
        if is_clk_en is True:
            self.m_to_s.extend([self.wr_clk_en, self.rd_clk_en])
        self.s_to_m = [self.rd_data, self.rd_data_valid]
        self.ports = self.m_to_s + self.s_to_m

        self.master = self.modport("master")
        self.slave = self.modport("slave")

        for port in self.m_to_s:
            self.master.set_output(port)
            self.slave.set_input(port)
        for port in self.s_to_m:
            self.master.set_input(port)
            self.slave.set_output(port)
