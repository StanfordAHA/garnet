import argparse
import magma
import coreir
from canal.util import IOSide
from gemstone.common.jtag_type import JTAGType
from gemstone.generator.generator import Generator
from global_controller.global_controller_magma import GlobalController
from global_controller.global_controller_wire_signal import\
    glc_interconnect_wiring
from global_buffer.global_buffer_magma import GlobalBuffer
from global_buffer.global_buffer_wire_signal import glb_glc_wiring, \
    glb_interconnect_wiring
from global_buffer.mmio_type import MMIOType
from canal.global_signal import GlobalSignalWiring
from lassen.sim import gen_pe
from cgra import create_cgra
import metamapper
import subprocess
import os
import math
import archipelago


class Garnet(Generator):
    def __init__(self, width, height, add_pd):
        super().__init__()

        # configuration parameters
        config_addr_width = 32
        config_data_width = 32
        tile_id_width = 16
        config_addr_reg_width = 8
        num_tracks = 5

        # only north side has IO
        io_side = IOSide.North

        # global buffer parameters
        num_banks = 32
        bank_addr = 17
        bank_data = 64
        glb_addr = math.ceil(math.log2(num_banks)) + bank_addr

        # SoC ctrl parameter
        soc_addr_width = 12

        # parallel configuration parameter
        num_parallel_cfg = math.ceil(width / 4)

        # number of input/output channels parameter
        num_io = math.ceil(width / 4)

        self.global_controller = GlobalController(config_addr_width,
                                                  config_data_width,
                                                  soc_addr_width)
        self.global_buffer = GlobalBuffer(num_banks=num_banks, num_io=num_io,
                                          num_cfg=num_parallel_cfg,
                                          bank_addr=bank_addr,
                                          top_cfg_addr=soc_addr_width)

        interconnect = create_cgra(width, height, io_side,
                                   reg_addr_width=config_addr_reg_width,
                                   config_data_width=config_data_width,
                                   tile_id_width=tile_id_width,
                                   num_tracks=num_tracks,
                                   add_pd=add_pd,
                                   global_signal_wiring
                                   =GlobalSignalWiring.ParallelMeso,
                                   num_parallel_config=num_parallel_cfg,
                                   mem_ratio=(1, 4))
        interconnect.dump_pnr("temp", "42")
        self.interconnect = interconnect

        self.add_ports(
            jtag=JTAGType,
            clk_in=magma.In(magma.Clock),
            reset_in=magma.In(magma.AsyncReset),
            soc_data=MMIOType(glb_addr, bank_data),
            soc_ctrl=MMIOType(soc_addr_width, config_data_width),
            soc_interrupt=magma.Out(magma.Bit),
        )

        # top <-> global controller ports connection
        self.wire(self.ports.jtag, self.global_controller.ports.jtag)
        self.wire(self.ports.clk_in, self.global_controller.ports.clk_in)
        self.wire(self.ports.reset_in, self.global_controller.ports.reset_in)
        self.wire(self.ports.soc_ctrl, self.global_controller.ports.soc_ctrl)
        self.wire(self.ports.soc_interrupt,
                  self.global_controller.ports.soc_interrupt)

        glc_interconnect_wiring(self)
        glb_glc_wiring(self)
        glb_interconnect_wiring(self, width, num_parallel_cfg)

        self.mapper_initalized = False

    def initialize_mapper(self):
        if self.mapper_initalized:
            raise RuntimeError("Can not initialize mapper twice")
        # Set up compiler and mapper.
        self.coreir_context = coreir.Context()
        self.mapper = metamapper.PeakMapper(self.coreir_context, "lassen")
        self.mapper.add_io_and_rewrite("io1", 1, "io2f_1", "f2io_1")
        self.mapper.add_io_and_rewrite("io16", 16, "io2f_16", "f2io_16")
        self.mapper.add_peak_primitive("PE", gen_pe)

        # Hack to speed up rewrite rules discovery.
        def bypass_mode(inst):
            return (
                inst.rega == type(inst.rega).BYPASS and
                inst.regb == type(inst.regb).BYPASS and
                inst.regd == type(inst.regd).BYPASS and
                inst.rege == type(inst.rege).BYPASS and
                inst.regf == type(inst.regf).BYPASS
            )
        self.mapper.add_discover_constraint(bypass_mode)

        self.mapper.discover_peak_rewrite_rules(width=16)

        self.mapper_initalized = True

    def map(self, halide_src):
        assert self.mapper_initalized
        app = self.coreir_context.load_from_file(halide_src)
        instrs = self.mapper.map_app(app)
        return app, instrs

    def run_pnr(self, info_file, mapped_file):
        cgra_path = os.getenv("CGRA_PNR", "")
        assert cgra_path != "", "Cannot find CGRA PnR"
        entry_point = os.path.join(cgra_path, "scripts", "pnr_flow.sh")
        subprocess.check_call([entry_point, info_file, mapped_file])

    def get_placement_bitstream(self, placement, id_to_name, instrs):
        result = []
        for node, (x, y) in placement.items():
            instance = id_to_name[node]
            if instance not in instrs:
                continue
            instr = instrs[instance]
            result += self.interconnect.configure_placement(x, y, instr)
        return result

    def convert_mapped_to_netlist(self, mapped):
        raise NotImplemented()

    def compile(self, halide_src):
        if not self.mapper_initalized:
            self.initialize_mapper()
        mapped, instrs = self.map(halide_src)
        # id to name converts the id to instance name
        netlist, bus, id_to_name = self.convert_mapped_to_netlist(mapped)
        placement, routing = archipelago.pnr(self.interconnect, (netlist, bus))
        bitstream = []
        bitstream += self.interconnect.get_route_bitstream(routing)
        bitstream += self.get_placement_bitstream(placement, id_to_name,
                                                  instrs)
        return bitstream

    def name(self):
        return "Garnet"


def main():
    parser = argparse.ArgumentParser(description='Garnet CGRA')
    parser.add_argument('--width', type=int, default=4)
    parser.add_argument('--height', type=int, default=2)
    parser.add_argument("--input-netlist", type=str, default="", dest="input")
    parser.add_argument("--output-bitstream", type=str, default="",
                        dest="output")
    parser.add_argument("-v", "--verilog", action="store_true")
    parser.add_argument("--no-pd", "--no-power-domain", action="store_true")
    args = parser.parse_args()

    assert args.width % 4 == 0 and args.width >= 4
    garnet = Garnet(width=args.width, height=args.height, add_pd=not args.no_pd)
    if args.verilog:
        garnet_circ = garnet.circuit()
        magma.compile("garnet", garnet_circ, output="coreir-verilog")
    if len(args.input) > 0 and len(args.output) > 0:
        # do PnR and produce bitstream
        bitstream = garnet.compile(args.input)
        with open(args.output, "w+") as f:
            bs = ["{0:08X} {1:08X}".format(entry[0], entry[1]) for entry
                  in bitstream]
            f.write("\n".join(bs))


if __name__ == "__main__":
    main()
