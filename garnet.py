import argparse
import magma
import coreir
from canal.util import IOSide
from gemstone.common.configurable import ConfigurationType
from gemstone.common.jtag_type import JTAGType
from gemstone.generator.generator import Generator
from global_controller.global_controller_magma import GlobalController
from global_controller.global_controller_wire_signal import\
    glc_interconnect_wiring
from global_buffer.global_buffer_magma import GlobalBuffer
from global_buffer.global_buffer_wire_signal import glb_glc_wiring, \
    glb_interconnect_wiring
from global_buffer.soc_data_type import SoCDataType
from global_controller.axi4_type import AXI4SlaveType
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
    def __init__(self, width, height, add_pd, interconnect_only: bool = False,
                 use_sram_stub: bool = True):
        super().__init__()

        # configuration parameters
        config_addr_width = 32
        config_data_width = 32
        axi_addr_width = 12
        tile_id_width = 16
        config_addr_reg_width = 8
        num_tracks = 5

        # only north side has IO
        io_side = IOSide.North

        # global buffer parameters
        num_banks = 32
        bank_addr_width = 17
        bank_data_width = 64
        glb_addr_width = 32

        # parallel configuration parameter
        num_parallel_cfg = math.ceil(width / 4)

        # number of input/output channels parameter
        num_io = math.ceil(width / 4)

        if not interconnect_only:
            wiring = GlobalSignalWiring.ParallelMeso
            self.global_controller = GlobalController(config_addr_width,
                                                      config_data_width,
                                                      axi_addr_width)

            self.global_buffer = GlobalBuffer(num_banks=num_banks,
                                              num_io=num_io,
                                              num_cfg=num_parallel_cfg,
                                              bank_addr_width=bank_addr_width,
                                              glb_addr_width=glb_addr_width,
                                              cfg_addr_width=config_addr_width,
                                              cfg_data_width=config_data_width,
                                              axi_addr_width=axi_addr_width)
        else:
            wiring = GlobalSignalWiring.Meso

        interconnect = create_cgra(width, height, io_side,
                                   reg_addr_width=config_addr_reg_width,
                                   config_data_width=config_data_width,
                                   tile_id_width=tile_id_width,
                                   num_tracks=num_tracks,
                                   add_pd=add_pd,
                                   use_sram_stub=use_sram_stub,
                                   global_signal_wiring=wiring,
                                   num_parallel_config=num_parallel_cfg,
                                   mem_ratio=(1, 4))

        self.interconnect = interconnect

        if not interconnect_only:
            self.add_ports(
                jtag=JTAGType,
                clk_in=magma.In(magma.Clock),
                reset_in=magma.In(magma.AsyncReset),
                soc_data=SoCDataType(glb_addr_width, bank_data_width),
                axi4_ctrl=AXI4SlaveType(axi_addr_width, config_data_width),
                cgra_running_clk_out=magma.Out(magma.Clock),
            )

            # top <-> global controller ports connection
            self.wire(self.ports.clk_in, self.global_controller.ports.clk_in)
            self.wire(self.ports.reset_in,
                      self.global_controller.ports.reset_in)
            self.wire(self.ports.jtag, self.global_controller.ports.jtag)
            self.wire(self.ports.axi4_ctrl,
                      self.global_controller.ports.axi4_ctrl)
            self.wire(self.ports.cgra_running_clk_out,
                      self.global_controller.ports.clk_out)

            # top <-> global buffer ports connection
            self.wire(self.ports.soc_data, self.global_buffer.ports.soc_data)
            glc_interconnect_wiring(self)
            glb_glc_wiring(self)
            glb_interconnect_wiring(self, width, num_parallel_cfg)
        else:
            # lift all the interconnect ports up
            self._lift_interconnect_ports(config_data_width)

        self.mapper_initalized = False
        self.__rewrite_rules = None

    def _lift_interconnect_ports(self, config_data_width):
        for name in self.interconnect.interface():
            self.add_port(name, self.interconnect.ports[name].type())
            self.wire(self.ports[name], self.interconnect.ports[name])
        self.add_ports(
            clk=magma.In(magma.Clock),
            reset=magma.In(magma.AsyncReset),
            config=magma.In(
                ConfigurationType(self.interconnect.config_data_width,
                                  self.interconnect.config_data_width)),
            stall=magma.In(
                magma.Bits[self.interconnect.stall_signal_width]),
            read_config_data=magma.Out(magma.Bits[config_data_width])
        )
        self.wire(self.ports.clk, self.interconnect.ports.clk)
        self.wire(self.ports.reset, self.interconnect.ports.reset)
        self.wire(self.ports.config,
                  self.interconnect.ports.config)
        self.wire(self.ports.stall,
                  self.interconnect.ports.stall)
        self.wire(self.interconnect.ports.read_config_data,
                  self.ports.read_config_data)

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
        self.mapper.map_app(app)
        instrs = self.mapper.extract_instr_map(app)
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
                #   after @perf branch is merged into master, we need to
                #   refactor the following code
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
        # get connections
        src_to_net_id = {}
        for conn in mapped.directed_module.connections:
            assert len(conn.source) == 2
            assert len(conn.sink) == 2
            src_name, src_port = conn.source
            dst_name, dst_port = conn.sink
            src_id = name_to_id[src_name]
            dst_id = name_to_id[dst_name]
            if (src_name, src_port) not in src_to_net_id:
                net_id = "e" + str(len(netlist))
                netlist[net_id] = [(src_id, src_port)]
                src_to_net_id[(src_name, src_port)] = net_id
            else:
                net_id = src_to_net_id[(src_name, src_port)]
            netlist[net_id].append((dst_id, dst_port))
            # get bus width
            src_instance = instances[src_name]
            width = src_instance.select(src_port).type.size
            if net_id in bus:
                assert bus[net_id] == width
            else:
                bus[net_id] = width

        id_to_name = {}
        for name, id in name_to_id.items():
            id_to_name[id] = name
        return netlist, bus, id_to_name

    @staticmethod
    def get_input_output(netlist):
        inputs = []
        outputs = []
        for _, net in netlist.items():
            for blk_id, port in net:
                if port == "io2f_16":
                    inputs.append(blk_id)
                elif port == "f2io_16":
                    outputs.append(blk_id)
                elif port == "io2f_1":
                    inputs.append(blk_id)
                elif port == "f2io_1":
                    outputs.append(blk_id)
        return inputs, outputs

    def get_io_interface(self, inputs, outputs, placement, id_to_name):
        input_interface = []
        output_interface = []
        reset_port_name = ""
        valid_port_name = ""

        for blk_id in inputs:
            x, y = placement[blk_id]
            bit_width = 16 if blk_id[0] == "I" else 1
            name = f"glb2io_{bit_width}_X{x:02X}_Y{y:02X}"
            input_interface.append(name)
            assert name in self.interconnect.interface()
            blk_name = id_to_name[blk_id]
            if "reset" in blk_name:
                reset_port_name = name
        for blk_id in outputs:
            x, y = placement[blk_id]
            bit_width = 16 if blk_id[0] == "I" else 1
            name = f"io2glb_{bit_width}_X{x:02X}_Y{y:02X}"
            output_interface.append(name)
            assert name in self.interconnect.interface()
            blk_name = id_to_name[blk_id]
            if "valid" in blk_name:
                valid_port_name = name
        return input_interface, output_interface,\
               (reset_port_name, valid_port_name)

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
        inputs, outputs = self.get_input_output(netlist)
        input_interface, output_interface, \
            (reset, valid) = self.get_io_interface(inputs,
                                                   outputs,
                                                   placement,
                                                   id_to_name)
        return bitstream, (input_interface, output_interface, reset, valid)

    def create_stub(self):
        result = """
module Garnet (
   input  clk,
   input [31:0] config_config_addr,
   input [31:0] config_config_data,
   input [0:0] config_read,
   input [0:0] config_write,
   output [31:0] read_config_data,
   input  reset,
   input [3:0] stall,
"""
        # loop through the interfaces
        ports = []
        for port_name, port_node in self.interconnect.interface().items():
            io = "output" if "io2glb" in port_name else "input"
            ports.append(f"   {io} [{port_node.width - 1}:0] {port_name}")
        result += ",\n".join(ports)
        result += "\n);\nendmodule\n"
        with open("garnet_stub.v", "w+") as f:
            f.write(result)

    def name(self):
        return "Garnet"


def main():
    parser = argparse.ArgumentParser(description='Garnet CGRA')
    parser.add_argument('--width', type=int, default=4)
    parser.add_argument('--height', type=int, default=2)
    parser.add_argument("--input-app", type=str, default="", dest="app")
    parser.add_argument("--input-file", type=str, default="", dest="input")
    parser.add_argument("--output-file", type=str, default="", dest="output")
    parser.add_argument("--gold-file", type=str, default="",
                        dest="gold")
    parser.add_argument("-v", "--verilog", action="store_true")
    parser.add_argument("--no-pd", "--no-power-domain", action="store_true")
    parser.add_argument("--rewrite-rules", type=str, default="")
    parser.add_argument("--interconnect-only", action="store_true")
    parser.add_argument("--no_sram_stub", action="store_true")
    args = parser.parse_args()
         
    if not args.interconnect_only:
        assert args.width % 4 == 0 and args.width >= 4
    garnet = Garnet(width=args.width, height=args.height,
                    add_pd=not args.no_pd,
                    interconnect_only=args.interconnect_only,
                    use_sram_stub=not args.no_sram_stub)

    if args.rewrite_rules:
        garnet.set_rewrite_rules(args.rewrite_rules)

    if args.verilog:
        garnet_circ = garnet.circuit()
        magma.compile("garnet", garnet_circ, output="coreir-verilog")
        garnet.create_stub()

    if len(args.app) > 0 and len(args.output) > 0:
        # do PnR and produce bitstream
        bitstream, (inputs, outputs, reset, valid) = garnet.compile(args.app)
        with open(args.output, "w+") as f:
            bs = ["{0:08X} {1:08X}".format(entry[0], entry[1]) for entry
                  in bitstream]
            f.write("\n".join(bs))

        # if input and gold is provided
        if len(args.input) > 0 and len(args.gold) > 0:
            # if we want to compare, write out the test configuration as well
            # write out the config file
            if len(inputs) > 1:
                inputs.remove(reset)
                assert len(inputs) == 1
            if len(outputs) > 1:
                outputs.remove(valid)
                assert len(outputs) == 1
            config = {
                "input_filename": args.input,
                "bitstream": args.output,
                "gold_filename": args.gold,
                "output_port_name": outputs[0],
                "input_port_name": inputs[0],
                "valid_port_name": valid,
                "reset_port_name": reset
            }
            with open(f"{args.output}.json", "w+") as f:
                json.dump(config, f)


if __name__ == "__main__":
    main()

