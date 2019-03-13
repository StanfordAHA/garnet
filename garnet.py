import argparse
import magma
import canal
from canal.cyclone import SwitchBoxSide, SwitchBoxIO
from canal.interconnect import Interconnect
from canal.global_signal import apply_global_meso_wiring
from canal.util import create_uniform_interconnect, SwitchBoxType
from gemstone.common.jtag_type import JTAGType
from gemstone.generator.generator import Generator
from global_controller.global_controller_magma import GlobalController
from memory_core.memory_core_magma import MemCore
from pe_core.pe_core_magma import PECore


class Garnet(Generator):
    def __init__(self, width, height):
        super().__init__()

        config_data_width = 32
        config_addr_width = 8
        tile_id_width = 16

        self.global_controller = GlobalController(32, 32)
        cores = {}
        for x in range(width):
            for y in range(height):
                core = MemCore(16, 1024) if (x % 2 == 1) else PECore()
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
        self.interconnect.finalize()
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

        self.__lift_ports()

    def __lift_ports(self):
        # FIXME: in old CGRAGenerator this is not necessary as ports can be
        #        driven by floating wires.
        #        unless a workaround is found, we need to lift all the SB
        #        ports. this will have lots of problems when interfacing with
        #        IO pads
        for port in self.interconnect.ports.values():
            port_name = port.qualified_name()
            if port_name[:2] == "SB":
                # lift the port up and connect to the interconnect core
                self.add_port(port_name, port.base_type())
                self.wire(self.ports[port_name], port)

    def map(self, halide_src, mapped_src):
        raise NotImplementedError()

    def run_pnr(self, info_file, mapped_file):
        raise NotImplementedError()

    def compile(self, halide_src):
        name = "my_app"
        self.map(halide_src, f"{name}.json")
        self.interconnect.dump_pnr("./", "garnet")
        self.run_pnr("garnet.info", f"{name}.json")
        placement = canal.io.load_placement_result(f"{name}.place")
        routing = canal.io.load_routing_result(f"{name}.place")
        bistream = []
        bitstream += self.interconnect.get_route_bitstream(routing)
        bitstream += self.get_placement_bitstream(placement)
        return bitstream

    def name(self):
        return "Garnet"


def main():
    parser = argparse.ArgumentParser(description='Garnet CGRA')
    parser.add_argument('--width', type=int, default=2)
    parser.add_argument('--height', type=int, default=2)
    args = parser.parse_args()

    garnet = Garnet(width=args.width, height=args.height)
    garnet_circ = garnet.circuit()
    magma.compile("garnet", garnet_circ, output="coreir-verilog")


if __name__ == "__main__":
    main()
