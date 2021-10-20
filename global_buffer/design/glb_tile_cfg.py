from kratos import Generator, verilog, always_comb
from .glb_cfg_ifc import GlbConfigInterface


class GlbTileCfg(Generator):
    def __init__(self, params):
        super().__init__("glb_tile_cfg")
        self.params = params
        config = GlbConfigInterface(self.params)

        # ports
        self.clk = self.clock("clk")
        self.reset = self.reset("reset", is_async=True)
        self.glb_tile_id = self.input(
            "glb_tile_id", self.params.tile_sel_addr_width)

        # config port
        self.if_cfg_wst_s = self.interface(
            config.slave, "if_cfg_wst_s", is_port=True)
        self.if_cfg_est_m = self.interface(
            config.master, "if_cfg_est_m", is_port=True)

        # register clear
        self.cfg_store_dma_invalidate_pulse = self.input("cfg_store_dma_invalidate_pulse",
                                                         width=1, size=self.params.queue_depth)
        self.cfg_load_dma_invalidate_pulse = self.output("cfg_load_dma_invalidate_pulse",
                                                         width=1, size=self.params.queue_depth)

        # configuration registers
        self.cfg_data_network_tile_connected = self.output(
            "cfg_data_network_tile_connected", 1)
        self.cfg_data_network_tile_connected = self.output(
            "cfg_data_network_tile_connected", 1)

