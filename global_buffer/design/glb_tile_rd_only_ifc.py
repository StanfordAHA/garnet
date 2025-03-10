from kratos import Interface
import math


class GlbTileReadOnlyInterface(Interface):
    def __init__(self, addr_width: int, data_width: int, num_tracks: int, is_clk_en=True):
        Interface.__init__(self, f"glb_tile_rd_only_ifc_A_{addr_width}_{num_tracks}xD_{data_width}")
        self.addr_width = addr_width
        self.data_width = data_width
        self.is_clk_en = is_clk_en

        # Local variables
        self.rd_en = self.var("rd_en", 1)
        if is_clk_en is True:
            self.rd_clk_en = self.var("rd_clk_en", 1)
        self.rd_addr = self.var("rd_addr", addr_width)


        self.rd_data = self.var("rd_data", data_width)
        # TODO: use this eventually
        # self.rd_data = self.var("rd_data", size=[data_width, num_tracks], packed=True)
        self.rd_data_valid = self.var("rd_data_valid", 1)

        self.m_to_s = [self.rd_en, self.rd_addr]
        if is_clk_en is True:
            self.m_to_s.extend([self.rd_clk_en])
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
