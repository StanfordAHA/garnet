import magma
import generator.generator as generator
from global_controller.global_controller_magma import GlobalController
from interconnect.cyclone import SwitchBoxSide, SwitchBoxIO
from interconnect.interconnect import Interconnect
from interconnect.global_signal import apply_global_meso_wiring
from interconnect.util import create_uniform_interconnect, SwitchBoxType
from pe_core.pe_core_magma import PECore
from memory_core.memory_core_magma import MemCore
from common.jtag_type import JTAGType


class CGRA(generator.Generator):
    def __init__(self, width, height):
        super().__init__()

        config_data_width = 32
        config_addr_width = 8
        tile_id_width = 16

        self.global_controller = GlobalController(32, 32)
        cores = {}
        for x in range(width):
            for y in range(height):
                core = MemCore(16, 1024) if (x % 4 == 3) else PECore()
                cores[(x, y)] = core

        def create_core(x_, y_):
            return cores[(x_, y_)]

        # specify input and output port connections
        inputs = ["data0", "data1", "bit0", "bit1", "bit2", "data_in",
                  "addr_in", "flush", "ren_in", "wen_in"]
        outputs = ["res", "res_p", "data_out"]
        # this is slightly different from the chip we tape out
        # here we connect input to every SB_IN and output to every SB_OUT
        port_conns = {}
        in_conn = []
        out_conn = []
        for side in SwitchBoxSide:
            in_conn.append((side, SwitchBoxIO.SB_IN))
            out_conn.append((side, SwitchBoxIO.SB_OUT))
        for input_port in inputs:
            port_conns[input_port] = in_conn
        for output_port in outputs:
            port_conns[output_port] = out_conn

        ic_graphs = {}
        for bit_width in [1, 16]:
            ic_graph = create_uniform_interconnect(width, height, bit_width,
                                                   create_core, port_conns,
                                                   {1: 5},
                                                   SwitchBoxType.Disjoint)
            ic_graphs[bit_width] = ic_graph

        self.interconnect = Interconnect(ic_graphs, config_addr_width,
                                         config_data_width, tile_id_width,
                                         lift_ports=True)
        # apply global wiring
        apply_global_meso_wiring(self.interconnect)

        self.add_ports(
            jtag=JTAGType,
            clk_in=magma.In(magma.Clock),
            reset_in=magma.In(magma.AsyncReset),
        )

        self.wire(self.ports.jtag, self.global_controller.ports.jtag)
        self.wire(self.ports.clk_in, self.global_controller.ports.clk_in)
        self.wire(self.ports.reset_in, self.global_controller.ports.reset_in)

        self.wire(self.global_controller.ports.config,
                  self.interconnect.ports.config)
        self.wire(self.global_controller.ports.clk_out,
                  self.interconnect.ports.clk)
        self.wire(self.global_controller.ports.reset_out,
                  self.interconnect.ports.reset)
        self.wire(self.global_controller.ports.stall,
                  self.interconnect.ports.stall)

        self.wire(self.interconnect.ports.read_config_data,
                  self.global_controller.ports.read_data_in)

    def name(self):
        return "CGRA"
