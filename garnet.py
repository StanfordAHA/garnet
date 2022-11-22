import argparse
import magma
from canal.util import IOSide
from gemstone.common.configurable import ConfigurationType
from gemstone.common.jtag_type import JTAGType
from gemstone.generator.generator import Generator, set_debug_mode
from global_buffer.io_placement import place_io_blk
from global_buffer.global_buffer_magma import GlobalBuffer
from global_controller.global_controller_magma import GlobalController
from cgra.ifc_struct import AXI4LiteIfc, ProcPacketIfc
from canal.global_signal import GlobalSignalWiring
from mini_mapper import map_app, has_rom, get_total_cycle_from_app
from cgra import glb_glc_wiring, glb_interconnect_wiring, \
        glc_interconnect_wiring, create_cgra, compress_config_data
import json
from passes.collateral_pass.config_register import get_interconnect_regs, \
    get_core_registers
from passes.interconnect_port_pass import stall_port_pass, config_port_pass
import math
import os
import archipelago
import archipelago.power
import archipelago.io

# set the debug mode to false to speed up construction
set_debug_mode(False)


class Garnet(Generator):
    def __init__(self, width, height, add_pd, interconnect_only: bool = False,
                 use_sram_stub: bool = True, standalone: bool = False,
                 add_pond: bool = True,
                 use_io_valid: bool = False,
                 pipeline_config_interval: int = 8,
                 glb_tile_mem_size: int = 256):
        super().__init__()

        # Check consistency of @standalone and @interconnect_only parameters. If
        # @standalone is True, then interconnect_only must also be True.
        if standalone:
            assert interconnect_only

        # configuration parameters
        config_addr_width = 32
        config_data_width = 32
        self.config_addr_width = config_addr_width
        self.config_data_width = config_data_width
        axi_addr_width = 13
        glb_axi_addr_width = 12
        axi_data_width = 32
        # axi_data_width must be same as cgra config_data_width
        assert axi_data_width == config_data_width

        tile_id_width = 16
        config_addr_reg_width = 8
        # num_tracks = 5
        num_tracks = 3


        # size
        self.width = width
        self.height = height

        # only north side has IO
        if standalone:
            io_side = IOSide.None_
        else:
            io_side = IOSide.North

        if not interconnect_only:
            # global buffer parameters
            # width must be even number
            assert (self.width % 2) == 0
            num_glb_tiles = self.width // 2

            bank_data_width = 64
            banks_per_tile = 2
            bank_addr_width = (magma.bitutils.clog2(glb_tile_mem_size)
                               - magma.bitutils.clog2(banks_per_tile) + 10)

            glb_addr_width = (bank_addr_width
                              + magma.bitutils.clog2(banks_per_tile)
                              + magma.bitutils.clog2(num_glb_tiles))

            # bank_data_width must be the size of bitstream
            assert bank_data_width == config_addr_width + config_data_width

            wiring = GlobalSignalWiring.ParallelMeso
            self.global_controller = GlobalController(addr_width=config_addr_width,
                                                      data_width=config_data_width,
                                                      axi_addr_width=axi_addr_width,
                                                      axi_data_width=axi_data_width,
                                                      num_glb_tiles=num_glb_tiles,
                                                      glb_addr_width=glb_addr_width,
                                                      glb_tile_mem_size=glb_tile_mem_size,
                                                      block_axi_addr_width=glb_axi_addr_width)

            self.global_buffer = GlobalBuffer(num_glb_tiles=num_glb_tiles,
                                              num_cgra_cols=width,
                                              glb_tile_mem_size=glb_tile_mem_size,
                                              bank_data_width=bank_data_width,
                                              cfg_addr_width=config_addr_width,
                                              cfg_data_width=config_data_width,
                                              axi_addr_width=glb_axi_addr_width,
                                              axi_data_width=axi_data_width)
        else:
            wiring = GlobalSignalWiring.Meso

        interconnect = create_cgra(width, height, io_side,
                                   reg_addr_width=config_addr_reg_width,
                                   config_data_width=config_data_width,
                                   tile_id_width=tile_id_width,
                                   num_tracks=num_tracks,
                                   add_pd=add_pd,
                                   add_pond=add_pond,
                                   use_io_valid=use_io_valid,
                                   use_sram_stub=use_sram_stub,
                                   global_signal_wiring=wiring,
                                   pipeline_config_interval=pipeline_config_interval,
                                   mem_ratio=(1, 4),
                                   standalone=standalone)

        self.interconnect = interconnect

        # make multiple stall ports
        stall_port_pass(self.interconnect)
        # make multiple configuration ports
        config_port_pass(self.interconnect)

        if not interconnect_only:
            self.add_ports(
                jtag=JTAGType,
                clk_in=magma.In(magma.Clock),
                reset_in=magma.In(magma.AsyncReset),
                proc_packet=ProcPacketIfc(glb_addr_width, bank_data_width).slave,
                axi4_slave=AXI4LiteIfc(axi_addr_width, axi_data_width).slave,
                interrupt=magma.Out(magma.Bit),
                cgra_running_clk_out=magma.Out(magma.Clock),
            )

            # top <-> global controller ports connection
            self.wire(self.ports.clk_in, self.global_controller.ports.clk_in)
            self.wire(self.ports.reset_in,
                      self.global_controller.ports.reset_in)
            self.wire(self.ports.jtag, self.global_controller.ports.jtag)
            self.wire(self.ports.axi4_slave,
                      self.global_controller.ports.axi4_slave)
            self.wire(self.ports.interrupt,
                      self.global_controller.ports.interrupt)
            self.wire(self.ports.cgra_running_clk_out,
                      self.global_controller.ports.clk_out)

            # top <-> global buffer ports connection
            self.wire(self.ports.clk_in, self.global_buffer.ports.clk)
            self.wire(self.ports.proc_packet, self.global_buffer.ports.proc_packet)

            # Top -> Interconnect clock port connection
            self.wire(self.ports.clk_in, self.interconnect.ports.clk)

            glb_glc_wiring(self)
            glb_interconnect_wiring(self)
            glc_interconnect_wiring(self)
        else:
            # lift all the interconnect ports up
            for name in self.interconnect.interface():
                self.add_port(name, self.interconnect.ports[name].type())
                self.wire(self.ports[name], self.interconnect.ports[name])

            self.add_ports(
                clk=magma.In(magma.Clock),
                reset=magma.In(magma.AsyncReset),
                config=magma.In(magma.Array[width,
                                ConfigurationType(config_data_width,
                                                  config_data_width)]),
                stall=magma.In(magma.Bits[self.width * self.interconnect.stall_signal_width]),
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

    def map(self, halide_src):
        return map_app(halide_src)

    def get_placement_bitstream(self, placement, id_to_name, instrs):
        result = []
        for node, (x, y) in placement.items():
            instance = id_to_name[node]
            if instance not in instrs:
                continue
            instr = instrs[instance]
            result += self.interconnect.configure_placement(x, y, instr,
                                                            node[0])
        return result

    def convert_mapped_to_netlist(self, mapped):
        raise NotImplemented()

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
        en_port_name = []

        for blk_id in inputs:
            x, y = placement[blk_id]
            bit_width = 16 if blk_id[0] == "I" else 1
            name = f"glb2io_{bit_width}_X{x:02X}_Y{y:02X}"
            input_interface.append(name)
            assert name in self.interconnect.interface()
            blk_name = id_to_name[blk_id]
            if "reset" in blk_name:
                reset_port_name = name
            if "in_en" in blk_name:
                en_port_name.append(name)
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
               (reset_port_name, valid_port_name, en_port_name)

    def compile(self, halide_src, unconstrained_io=False, compact=False):
        id_to_name, instance_to_instr, netlist, bus = self.map(halide_src)
        app_dir = os.path.dirname(halide_src)
        if unconstrained_io:
            fixed_io = None
        else:
            fixed_io = place_io_blk(id_to_name)
        placement, routing = archipelago.pnr(self.interconnect, (netlist, bus),
                                             cwd="temp",
                                             id_to_name=id_to_name,
                                             fixed_pos=fixed_io,
                                             compact=compact,
                                             copy_to_dir=app_dir)
        routing_fix = archipelago.power.reduce_switching(routing, self.interconnect,
                                                         compact=compact)
        routing.update(routing_fix)
        bitstream = []
        bitstream += self.interconnect.get_route_bitstream(routing)
        bitstream += self.get_placement_bitstream(placement, id_to_name,
                                                  instance_to_instr)
        skip_addr = self.interconnect.get_skip_addr()
        bitstream = compress_config_data(bitstream, skip_compression=skip_addr)
        inputs, outputs = self.get_input_output(netlist)
        input_interface, output_interface,\
            (reset, valid, en) = self.get_io_interface(inputs,
                                                       outputs,
                                                       placement,
                                                       id_to_name)
        delay = 1 if has_rom(id_to_name) else 0
        # also write out the meta file
        archipelago.io.dump_meta_file(halide_src, "design", os.path.dirname(halide_src))
        return bitstream, (input_interface, output_interface, reset, valid, en,
                           delay)

    def compile_virtualize(self, halide_src, max_group):
        id_to_name, instance_to_instr, netlist, bus = self.map(halide_src)
        partition_result = archipelago.pnr_virtualize(self.interconnect, (netlist, bus), cwd="temp",
                                                      id_to_name=id_to_name, max_group=max_group)
        result = {}
        for c_id, ((placement, routing), p_id_to_name) in partition_result.items():
            bitstream = []
            bitstream += self.interconnect.get_route_bitstream(routing)
            bitstream += self.get_placement_bitstream(placement, p_id_to_name,
                                                      instance_to_instr)
            skip_addr = self.interconnect.get_skip_addr()
            bitstream = compress_config_data(bitstream, skip_compression=skip_addr)
            result[c_id] = bitstream
        return result

    def create_stub(self):
        result = """
module Interconnect (
   input  clk,
   output [31:0] read_config_data,
   input  reset,
"""
        # add stall based on the size
        result += f"   input [{str(self.width * self.interconnect.stall_signal_width - 1)}:0] stall,\n\n"
        # magma can't generate SV struct array, which would be the ideal solution here
        for i in range(self.width):
            result += f"   input [31:0] config_{i}_config_addr,\n"
            result += f"   input [31:0] config_{i}_config_data,\n"
            result += f"   input [0:0] config_{i}_read,\n"
            result += f"   input [0:0] config_{i}_write,\n"
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


def write_out_bitstream(filename, bitstream):
    with open(filename, "w+") as f:
        bs = ["{0:08X} {1:08X}".format(entry[0], entry[1]) for entry
              in bitstream]
        f.write("\n".join(bs))


def main():
    parser = argparse.ArgumentParser(description='Garnet CGRA')
    parser.add_argument('--width', type=int, default=4)
    parser.add_argument('--height', type=int, default=2)
    parser.add_argument('--pipeline_config_interval', type=int, default=8)
    parser.add_argument('--glb_tile_mem_size', type=int, default=256)
    parser.add_argument("--input-app", type=str, default="", dest="app")
    parser.add_argument("--input-file", type=str, default="", dest="input")
    parser.add_argument("--output-file", type=str, default="", dest="output")
    parser.add_argument("--gold-file", type=str, default="",
                        dest="gold")
    parser.add_argument("-v", "--verilog", action="store_true")
    parser.add_argument("--no-pd", "--no-power-domain", action="store_true")
    parser.add_argument("--no-pond", action="store_true")
    parser.add_argument("--interconnect-only", action="store_true")
    parser.add_argument("--compact", action="store_true")
    parser.add_argument("--no-sram-stub", action="store_true")
    parser.add_argument("--standalone", action="store_true")
    parser.add_argument("--unconstrained-io", action="store_true")
    parser.add_argument("--dump-config-reg", action="store_true")
    parser.add_argument("--virtualize-group-size", type=int, default=4)
    parser.add_argument("--virtualize", action="store_true")
    parser.add_argument("--use-io-valid", action="store_true")
    args = parser.parse_args()

    if not args.interconnect_only:
        assert args.width % 2 == 0 and args.width >= 4
    if args.standalone and not args.interconnect_only:
        raise Exception("--standalone must be specified with "
                        "--interconnect-only as well")
    garnet = Garnet(width=args.width, height=args.height,
                    glb_tile_mem_size=args.glb_tile_mem_size,
                    add_pd=not args.no_pd,
                    pipeline_config_interval=args.pipeline_config_interval,
                    add_pond=not args.no_pond,
                    use_io_valid=args.use_io_valid,
                    interconnect_only=args.interconnect_only,
                    use_sram_stub=not args.no_sram_stub,
                    standalone=args.standalone)

    if args.verilog:
        garnet_circ = garnet.circuit()
        magma.compile("garnet", garnet_circ, output="coreir-verilog",
                      coreir_libs={"float_CW"},
                      passes = ["rungenerators", "inline_single_instances", "clock_gate"],
                      disable_ndarray=True,
                      inline=False)
        garnet.create_stub()
    if len(args.app) > 0 and len(args.input) > 0 and len(args.gold) > 0 \
            and len(args.output) > 0 and not args.virtualize:
        # do PnR and produce bitstream
        bitstream, (inputs, outputs, reset, valid, \
            en, delay) = garnet.compile(args.app, args.unconstrained_io, compact=args.compact)
        # write out the config file
        if len(inputs) > 1:
            if reset in inputs:
                inputs.remove(reset)
            for en_port in en:
                if en_port in inputs:
                    inputs.remove(en_port)
        total_cycle = get_total_cycle_from_app(args.app)
        if len(outputs) > 1:
            outputs.remove(valid)
        config = {
            "input_filename": args.input,
            "bitstream": args.output,
            "gold_filename": args.gold,
            "output_port_name": outputs,
            "input_port_name": inputs,
            "valid_port_name": valid,
            "reset_port_name": reset,
            "en_port_name": en,
            "delay": delay,
            "total_cycle": total_cycle
        }
        with open(f"{args.output}.json", "w+") as f:
            json.dump(config, f)
        write_out_bitstream(args.output, bitstream)
    elif args.virtualize and len(args.app) > 0:
        group_size = args.virtualize_group_size
        result = garnet.compile_virtualize(args.app, group_size)
        for c_id, bitstream in result.items():
            filename = os.path.join("temp", f"{c_id}.bs")
            write_out_bitstream(filename, bitstream)
    if args.dump_config_reg:
        ic = garnet.interconnect
        ic_reg = get_interconnect_regs(ic)
        core_reg = get_core_registers(ic)
        with open("config.json", "w+") as f:
            json.dump(ic_reg + core_reg, f)


if __name__ == "__main__":
    main()

