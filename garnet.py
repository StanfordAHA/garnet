import argparse
import magma
import canal
import coreir
from canal.cyclone import SwitchBoxSide, SwitchBoxIO
from canal.interconnect import Interconnect
from canal.global_signal import apply_global_meso_wiring
from canal.util import create_uniform_interconnect, SwitchBoxType
from gemstone.common.jtag_type import JTAGType
from gemstone.generator.generator import Generator
from global_controller.global_controller_magma import GlobalController
from memory_core.memory_core_magma import MemCore
from lassen.sim import gen_pe
from peak_core.peak_core import PeakCore
from io_core.io1bit_magma import IO1bit
from io_core.io16bit_magma import IO16bit
import metamapper
import subprocess
import os


class Garnet(Generator):
    def __init__(self, width, height):
        super().__init__()

        config_data_width = 32
        config_addr_width = 8
        tile_id_width = 16
        num_tracks = 5

        self.global_controller = GlobalController(32, 32)
        cores = {}
        margin = 1
        # Use the new height due to the margin.
        width += 2 * margin
        height += 2 * margin

        cores = {}
        for x in range(width):
            for y in range(height):
                # Empty corner.
                if x in range(margin) and y in range(margin):
                    core = None
                elif x in range(margin) and y in range(height - margin,
                                                       height):
                    core = None
                elif x in range(width - margin,
                                width) and y in range(margin):
                    core = None
                elif x in range(width - margin,
                                width) and y in range(height - margin,
                                                      height):
                    core = None
                elif x in range(margin) \
                        or x in range(width - margin, width) \
                        or y in range(margin) \
                        or y in range(height - margin, height):
                    if x == margin or y == margin:
                        core = IO16bit()
                    else:
                        core = IO1bit()
                else:
                    core = MemCore(16, 1024) if ((x - margin) % 2 == 1) else \
                        PeakCore(gen_pe)
                cores[(x, y)] = core

        def create_core(xx: int, yy: int):
            return cores[(xx, yy)]

        # Specify input and output port connections.
        inputs = set()
        outputs = set()
        for core in cores.values():
            # Skip IO cores.
            if core is None or isinstance(core, (IO1bit, IO16bit)):
                continue
            inputs |= {i.qualified_name() for i in core.inputs()}
            outputs |= {o.qualified_name() for o in core.outputs()}

        # This is slightly different from the original CGRA. Here we connect
        # input to every SB_IN and output to every SB_OUT.
        port_conns = {}
        in_conn = [(side, SwitchBoxIO.SB_IN) for side in SwitchBoxSide]
        out_conn = [(side, SwitchBoxIO.SB_OUT) for side in SwitchBoxSide]
        port_conns.update({input_: in_conn for input_ in inputs})
        port_conns.update({output: out_conn for output in outputs})

        ic_graphs = {}
        io_in = {"f2io_1": [1], "f2io_16": [0]}
        io_out = {"io2f_1": [1], "io2f_16": [0]}
        io_conn = {"in": io_in, "out": io_out}
        pipeline_regs = []
        for track in range(num_tracks):
            for side in SwitchBoxSide:
                pipeline_regs.append((track, side))
        for bit_width in (1, 16):
            ic_graph = create_uniform_interconnect(width, height, bit_width,
                                                   create_core, port_conns,
                                                   {1: num_tracks},
                                                   SwitchBoxType.Disjoint,
                                                   pipeline_regs,
                                                   margin=margin,
                                                   io_conn=io_conn)
            ic_graphs[bit_width] = ic_graph

        lift_ports = margin == 0
        self.interconnect = Interconnect(ic_graphs, config_addr_width,
                                         config_data_width, tile_id_width,
                                         lift_ports=lift_ports)
        self.interconnect.finalize()

        # Apply global wiring.
        apply_global_meso_wiring(self.interconnect, margin=margin)

        # Lift interconnect ports.
        for name in self.interconnect.interface():
            self.add_port(name, self.interconnect.ports[name].type())
            self.wire(self.ports[name], self.interconnect.ports[name])

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

        # Set up compiler and mapper.
        self.coreir_context = coreir.Context()
        mapper = metamapper.PeakMapper(self.coreir_context, "lassen")
        mapper.add_io_and_rewrite("io16", 16, "tofab", "fromfab")
        mapper.add_io_and_rewrite("io1", 1, "tofab", "fromfab")
        mapper.add_peak_primitive("PE", gen_pe)
        mapper.discover_peak_rewrite_rules(width=16)

    def map(self, halide_src):
        app = self.coreir_context.load_from_file(halide_src)
        instrs = mapper.map_app(app)
        return app, instrs

    @staticmethod
    def run_pnr(info_file, mapped_file):
        cgra_path = os.getenv("CGRA_PNR", "")
        assert cgra_path != "", "Cannot find CGRA PnR"
        entry_point = os.path.join(cgra_path, "scripts", "pnr_flow.sh")
        subprocess.check_call([entry_point, info_file, mapped_file])

    def get_placement_bitstream(self, placement):
        raise NotImplementedError()

    def compile(self, halide_src):
        mapped, instrs = self.map(halide_src)
        mapped.save_to_file(mapped, "./app.json")
        self.interconnect.dump_pnr("./", "garnet")
        self.run_pnr("garnet.info", "./app.json")
        p = canal.io.load_placement_result("app.place")
        r = canal.io.load_routing_result(f"app.route")
        bistream = []
        bitstream += self.interconnect.get_route_bitstream(r)
        bitstream += self.get_placement_bitstream(p)
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
