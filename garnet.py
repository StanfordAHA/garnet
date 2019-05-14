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
import json
from lassen import rules as lassen_rewrite_rules
from lassen import LassenMapper

from io_core.io_core_magma import IOCore
from peak_core.peak_core import PeakCore


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
        self.__rewrite_rules = None

    def set_rewrite_rules(self,rewrite_rules):
        self.__rewrite_rules = rewrite_rules

    def initialize_mapper(self, rewrite_rules=None,discover=False):
        if self.mapper_initalized:
            raise RuntimeError("Can not initialize mapper twice")
        # Set up compiler and mapper.
        self.coreir_context = coreir.Context()

        #Initializes with all the custom rewrite rules
        self.mapper = LassenMapper(self.coreir_context)

        # Either load rewrite rules from cached file or generate them by
        # discovery.
        if rewrite_rules:
            with open(rewrite_rules) as jfile:
                rules = json.load(jfile)
            for rule in rules:
                self.mapper.add_rr_from_description(rule)
        elif discover:
            # Hack to speed up rewrite rules discovery.
            bypass_mode = lambda inst: (
                inst.rega == type(inst.rega).BYPASS and
                inst.regb == type(inst.regb).BYPASS and
                inst.regd == type(inst.regd).BYPASS and
                inst.rege == type(inst.rege).BYPASS and
                inst.regf == type(inst.regf).BYPASS
            )
            self.mapper.add_discover_constraint(bypass_mode)
            self.mapper.discover_peak_rewrite_rules(width=16)
        else:
            for rule in lassen_rewrite_rules:
                self.mapper.add_rr_from_description(rule)

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

    @staticmethod
    def __instance_to_int(mod: coreir.module.Module):
        top_def = mod.definition
        result = {}
        instances = {}

        for instance in top_def.instances:
            instance_name = instance.name
            assert instance_name not in result
            result[instance_name] = str(len(result))
            instances[instance_name] = instance
        return result, instances

    def __get_available_cores(self):
        result = {}
        for tile in self.interconnect.tile_circuits.values():
            core = tile.core
            tags = core.pnr_info()
            if not isinstance(tags, list):
                tags = [tags]
            for tag in tags:
                if tag.tag_name not in result:
                    result[tag.tag_name] = tag, core
        return result

    def convert_mapped_to_netlist(self, mapped):
        instance_id, instances = self.__instance_to_int(mapped)
        core_tags = self.__get_available_cores()
        name_to_id = {}
        module_name_to_tag = {}
        netlist = {}
        bus = {}
        # map instances to tags
        for instance_name, instance in instances.items():
            module_name = instance.module.name
            if module_name == "PE":
                # it's a PE core
                # FIXME: because generators are not hashable, we can't reverse
                #   index table search the tags
                if module_name not in module_name_to_tag:
                    instance_tag = ""
                    for tag_name, (tag, core) in core_tags.items():
                        if isinstance(core, PeakCore):
                            instance_tag = tag_name
                            break
                    assert instance_tag != "", "Cannot find the core"
                    module_name_to_tag[module_name] = instance_tag
            elif instance.module.name == "io16":
                # it's an IO core
                if module_name not in module_name_to_tag:
                    instance_tag = ""
                    for tag_name, (tag, core) in core_tags.items():
                        if isinstance(core, IOCore):
                            instance_tag = tag_name
                            break
                    assert instance_tag != "", "Cannot find the core"
                    module_name_to_tag[module_name] = instance_tag
            else:
                raise ValueError(f"Cannot find CGRA core for {module_name}. "
                                 f"Is the mapper working?")

            name_to_id[instance_name] = module_name_to_tag[module_name] + \
                instance_id[instance_name]
        return netlist, bus, name_to_id

    def compile(self, halide_src):
        if not self.mapper_initalized:
            self.initialize_mapper(self.__rewrite_rules)
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
    parser.add_argument("--rewrite-rules", type=str, default="")
    args = parser.parse_args()

    assert args.width % 4 == 0 and args.width >= 4
    garnet = Garnet(width=args.width, height=args.height, add_pd=not args.no_pd)
    if args.rewrite_rules:
        garnet.set_rewrite_rules(args.rewrite_rules)
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
