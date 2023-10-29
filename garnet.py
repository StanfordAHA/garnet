import os
if os.getenv('WHICH_SOC') == "amber":
    import garnet_amber
    if __name__ == "__main__": garnet_amber.main()
    exit()

import argparse
import magma
from systemRDL.util import gen_rdl_header # If I move this it breaks. Dunno why.
from cgra import compress_config_data
import json
import archipelago
import archipelago.power
import archipelago.io
from lassen.sim import PE_fc as lassen_fc
# from metamapper.coreir_mapper import Mapper # Not used??
# from canal.global_signal import GlobalSignalWiring


# set the debug mode to false to speed up construction
from gemstone.generator.generator import set_debug_mode
set_debug_mode(False)


from gemstone.generator.generator import Generator
class Garnet(Generator):
    def __init__(self, args):
        super().__init__()

        # args.add_pd = not args.no_pd

        # Check consistency of @standalone and @interconnect_only parameters. If
        # @standalone is True, then interconnect_only must also be True.
        if args.standalone:
            assert interconnect_only

        # configuration parameters
        self.glb_params = args.glb_params
        self.config_addr_width = 32
        self.config_data_width = 32

        self.amber_pond = args.amber_pond

        args.tile_id_width = 16
        args.config_addr_reg_width = 8

        # size
        self.width = args.width
        self.height = args.height

        self.pe_fc = args.pe_fc
        self.harden_flush = args.harden_flush
        self.pipeline_config_interval = args.pipeline_config_interval

        # only north side has IO
        from canal.util import IOSide
        if args.standalone: io_side = IOSide.None_
        else:               io_side = IOSide.North


        # Build GLB unless interconnect_only (CGRA-only) requested

        # Tried moving this down to other interconnect_only clause;
        # pytests passed but RTL was different :(
        if not args.interconnect_only:
            self.build_glb()  # Builds self.{global_controller, global_buffer}

        width             = args.width
        height            = args.height

        # BUILD THE CGRA

        from cgra import create_cgra_w_args
        args.config_data_width = self.config_data_width
        self.interconnect = create_cgra_w_args(width, height, io_side, args)

        # Add stall, flush, and configuration ports

        from passes.interconnect_port_pass import stall_port_pass, config_port_pass
        # make multiple stall ports
        stall_port_pass(self.interconnect, port_name="stall", port_width=1, col_offset=1)
        # make multiple flush ports
        if self.harden_flush:
            stall_port_pass(self.interconnect, port_name="flush", port_width=1,
                            col_offset=args.glb_params.num_cols_per_group, pipeline=True)
        # make multiple configuration ports
        config_port_pass(self.interconnect, pipeline=args.config_port_pipeline)

        # Core connections

        self.inter_core_connections = {}
        for bw, interconnect in self.interconnect._Interconnect__graphs.items():
            self.inter_core_connections[bw] = interconnect.inter_core_connection

        # GLB ports (or not)

        # interconnect_only = args.interconnect_only
        print(f'--- IC {args.interconnect_only}')
        if not args.interconnect_only:
            self.build_glb_ports(args.glb_params)
        else:
            self.lift_ports(self.width, self.config_data_width, self.harden_flush)


    def build_glb(self):
            import math
            from global_controller.global_controller_magma import GlobalController
            from global_buffer.design.global_buffer import GlobalBufferMagma

            glb_params = self.glb_params

            # axi_data_width must be same as cgra config_data_width
            axi_addr_width = self.glb_params.cgra_axi_addr_width
            axi_data_width = self.glb_params.axi_data_width
            assert axi_data_width == self.config_data_width

            # width must be even number
            assert (self.width % 2) == 0

            # Bank should be larger than or equal to 1KB
            assert glb_params.bank_addr_width >= 10

            glb_tile_mem_size = 2 ** (glb_params.bank_addr_width - 10) + \
                math.ceil(math.log(glb_params.banks_per_tile, 2))

            self.global_controller = GlobalController(addr_width=self.config_addr_width,
                                                      data_width=self.config_data_width,
                                                      axi_addr_width=axi_addr_width,
                                                      axi_data_width=axi_data_width,
                                                      num_glb_tiles=glb_params.num_glb_tiles,
                                                      cgra_width=glb_params.num_cgra_cols,
                                                      glb_addr_width=glb_params.glb_addr_width,
                                                      glb_tile_mem_size=glb_tile_mem_size,
                                                      block_axi_addr_width=glb_params.axi_addr_width,
                                                      group_size=glb_params.num_cols_per_group)

            self.global_buffer = GlobalBufferMagma(glb_params)



    def build_glb_ports(self, glb_params):

            # axi_data_width must be same as cgra config_data_width
            axi_addr_width = self.glb_params.cgra_axi_addr_width
            axi_data_width = self.glb_params.axi_data_width
            assert axi_data_width == self.config_data_width

            from gemstone.common.jtag_type import JTAGType
            from cgra.ifc_struct import AXI4LiteIfc, ProcPacketIfc
            self.add_ports(
                jtag=JTAGType,
                clk_in=magma.In(magma.Clock),
                reset_in=magma.In(magma.AsyncReset),
                proc_packet=ProcPacketIfc(
                    glb_params.glb_addr_width, glb_params.bank_data_width).slave,
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
            self.wire(self.ports.proc_packet.wr_en,
                      self.global_buffer.ports.proc_wr_en[0])
            self.wire(self.ports.proc_packet.wr_strb,
                      self.global_buffer.ports.proc_wr_strb)
            self.wire(self.ports.proc_packet.wr_addr,
                      self.global_buffer.ports.proc_wr_addr)
            self.wire(self.ports.proc_packet.wr_data,
                      self.global_buffer.ports.proc_wr_data)
            self.wire(self.ports.proc_packet.rd_en,
                      self.global_buffer.ports.proc_rd_en[0])
            self.wire(self.ports.proc_packet.rd_addr,
                      self.global_buffer.ports.proc_rd_addr)
            self.wire(self.ports.proc_packet.rd_data,
                      self.global_buffer.ports.proc_rd_data)
            self.wire(self.ports.proc_packet.rd_data_valid,
                      self.global_buffer.ports.proc_rd_data_valid[0])

            # Top -> Interconnect clock port connection
            self.wire(self.ports.clk_in, self.interconnect.ports.clk)

            from cgra import glb_glc_wiring, glb_interconnect_wiring, glc_interconnect_wiring
            glb_glc_wiring(self)
            glb_interconnect_wiring(self)
            glc_interconnect_wiring(self)

    def lift_ports(self, width, config_data_width, harden_flush):
            # lift all the interconnect ports up
            for name in self.interconnect.interface():
                self.add_port(name, self.interconnect.ports[name].type())
                self.wire(self.ports[name], self.interconnect.ports[name])

            from gemstone.common.configurable import ConfigurationType
            self.add_ports(
                clk=magma.In(magma.Clock),
                reset=magma.In(magma.AsyncReset),
                config=magma.In(magma.Array[width,
                                ConfigurationType(config_data_width,
                                                  config_data_width)]),
                stall=magma.In(
                    magma.Bits[self.width * self.interconnect.stall_signal_width]),
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

            if harden_flush:
                self.add_ports(flush=magma.In(magma.Bits[self.width // 4]))
                self.wire(self.ports.flush, self.interconnect.ports.flush)




    from mini_mapper import map_app
    def map(self, halide_src):
        return map_app(halide_src, retiming=True)

    def get_placement_bitstream(self, placement, id_to_name, instrs):
        result = []
        for node, (x, y) in placement.items():
            instance = id_to_name[node]
            if instance not in instrs:
                continue
            instr = instrs[instance]
            result += self.interconnect.configure_placement(x, y, instr,
                                                            node[0])
            if node in self.pes_with_packed_ponds:
                print(f"pond {self.pes_with_packed_ponds[node]} being packed with {node} in {x},{y}")
                node = self.pes_with_packed_ponds[node]
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
            bit_width = 17 if blk_id[0] == "I" else 1
            #bit_width = 16 if blk_id[0] == "I" else 1
            name = f"glb2io_{bit_width}_X{x:02X}_Y{y:02X}"
            input_interface.append(name)
            print("WEIRD NAME ASSERTION")
            print(name)
            print(self.interconnect.interface())
            assert name in self.interconnect.interface()
            blk_name = id_to_name[blk_id]
            if "reset" in blk_name:
                reset_port_name = name
            if "in_en" in blk_name:
                en_port_name.append(name)
        for blk_id in outputs:
            x, y = placement[blk_id]
            #bit_width = 16 if blk_id[0] == "I" else 1
            bit_width = 17 if blk_id[0] == "I" else 1
            name = f"io2glb_{bit_width}_X{x:02X}_Y{y:02X}"
            output_interface.append(name)
            assert name in self.interconnect.interface()
            blk_name = id_to_name[blk_id]
            if "valid" in blk_name:
                valid_port_name = name
        return input_interface, output_interface,\
            (reset_port_name, valid_port_name, en_port_name)

    def pack_ponds(self, netlist_info):
        packed_ponds = {}

        for edge_id in list(netlist_info['netlist']):
            conns = netlist_info['netlist'][edge_id]
            bw = netlist_info["buses"][edge_id]
            inter_core_conns = self.inter_core_connections[bw]
            (source, source_port) = conns[0]
            for (sink, sink_port) in conns[1:]:
                if source_port in inter_core_conns and source[0] == "M":
                    if sink_port in inter_core_conns[source_port] and sink[0] == 'p':
                        packed_ponds[source] = sink

        for edge_id, conns in netlist_info['netlist'].items():
            new_conns = []
            for conn in conns:
                if conn[0] in packed_ponds:
                    new_conns.append((packed_ponds[conn[0]], conn[1]))
                else:
                    new_conns.append(conn)
            netlist_info['netlist'][edge_id] = new_conns

        self.pes_with_packed_ponds = {pe:pond for pond,pe in packed_ponds.items()}

    def load_netlist(self, app, load_only, pipeline_input_broadcasts,
                     input_broadcast_branch_factor, input_broadcast_max_leaves):

        import metamapper.coreir_util as cutil
        from metamapper import CoreIRContext
        from metamapper.irs.coreir import gen_CoreIRNodes
        from metamapper.io_tiles import IO_fc, BitIO_fc
        import metamapper.peak_util as putil
        from mapper.netlist_util import create_netlist_info, print_netlist_info

        app_dir = os.path.dirname(app)

        if self.pe_fc == lassen_fc:
            pe_header = f"{app_dir}/lassen_header.json"
        else:
            pe_header = f"{app_dir}/pe_header.json"

        mem_header = f"{app_dir}/mem_header.json"
        io_header = f"{app_dir}/io_header.json"
        bit_io_header = f"{app_dir}/bit_io_header.json"
        pond_header = f"{app_dir}/pond_header.json"

        app_file = app
        c = CoreIRContext(reset=True)
        cutil.load_libs(["cgralib"])
        cmod = cutil.load_from_json(app_file)
        c = CoreIRContext()
        cutil.load_libs(["cgralib", "commonlib", "float"])
        c.run_passes(["flatten"])

        nodes = gen_CoreIRNodes(16)

        putil.load_and_link_peak(
            nodes,
            pe_header,
            {"global.PE": self.pe_fc},
        )

        putil.load_and_link_peak(
            nodes,
            io_header,
            {"global.IO": IO_fc},
        )

        putil.load_and_link_peak(
            nodes,
            bit_io_header,
            {"global.BitIO": BitIO_fc},
        )

        dag = cutil.coreir_to_dag(nodes, cmod)
        tile_info = {"global.PE": self.pe_fc, "cgralib.Mem": nodes.peak_nodes["cgralib.Mem"],
                     "global.IO": IO_fc, "global.BitIO": BitIO_fc, "cgralib.Pond": nodes.peak_nodes["cgralib.Pond"]}
        netlist_info = create_netlist_info(app_dir,
                                           dag,
                                           tile_info,
                                           load_only,
                                           self.harden_flush,
                                           1 + self.height // self.pipeline_config_interval,
                                           pipeline_input_broadcasts,
                                           input_broadcast_branch_factor,
                                           input_broadcast_max_leaves)

        mem_remap = None
        pe_remap = None
        
        for core_key, core_value in self.interconnect.tile_circuits.items():
            actual_core = core_value.core
            pnr_tag = actual_core.pnr_info()
            if isinstance(pnr_tag, list):
                continue
            pnr_tag = pnr_tag.tag_name
            if pnr_tag == "m" and mem_remap is None:
                mem_remap = actual_core.get_port_remap()
            elif pnr_tag == "p" and pe_remap is None:
                pe_remap = actual_core.get_port_remap()
            elif mem_remap is not None and pe_remap is not None:
                break

        for netlist_id, connections_list in netlist_info['netlist'].items():
            for idx, connection in enumerate(connections_list):
                tag_, pin_ = connection
                if tag_[0] == 'm':
                    # get mode...
                    metadata = netlist_info['id_to_metadata'][tag_]
                    mode = "UB"
                    if 'stencil_valid' in metadata["config"]:
                        mode = 'stencil_valid'
                    elif 'mode' in metadata and metadata['mode'] == 'sram':
                        mode = 'ROM'
                        # Actually use wr addr for rom mode...
                        hack_remap = {
                            'addr_in_0': 'wr_addr_in',
                            'ren_in_0': 'ren',
                            'data_out_0': 'data_out'
                                }
                        assert pin_ in hack_remap
                        pin_ = hack_remap[pin_]
                    pin_remap = mem_remap[mode][pin_]
                    connections_list[idx] = (tag_, pin_remap)
                elif tag_[0] == 'p':
                    pin_remap = pe_remap['alu'][pin_]
                    connections_list[idx] = (tag_, pin_remap)
            netlist_info['netlist'][netlist_id] = connections_list

        if not self.amber_pond:
            # temporally remapping of port names for the new Pond
            for name, mapping in netlist_info["netlist"].items():
                for i in range(len(mapping)):
                    (inst_name, port_name) = mapping[i]
                    if "data_in_pond_0" in port_name:
                        mapping[i] = (inst_name, "PondTop_input_width_17_num_0")
                    if "data_out_pond_0" in port_name:
                        mapping[i] = (inst_name, "PondTop_output_width_17_num_0")
                    if "data_in_pond_1" in port_name:
                        mapping[i] = (inst_name, "PondTop_input_width_17_num_1")
                    if "data_out_pond_1" in port_name:
                        mapping[i] = (inst_name, "PondTop_output_width_17_num_1")


        self.pack_ponds(netlist_info)

        port_remap_fout = open(app_dir + "/design.port_remap", "w")
        port_remap_fout.write(json.dumps(pe_remap['alu']))
        port_remap_fout.close()
        
        print_netlist_info(netlist_info, self.pes_with_packed_ponds, app_dir + "/netlist_info.txt")

        return (netlist_info["id_to_name"], netlist_info["instance_to_instrs"], netlist_info["netlist"],
                netlist_info["buses"])

    def place_and_route(self, halide_src, unconstrained_io=False, compact=False, load_only=False,
                        pipeline_input_broadcasts=False, input_broadcast_branch_factor=4,
                        input_broadcast_max_leaves=16):
        id_to_name, instance_to_instr, netlist, bus = self.load_netlist(halide_src,
                                                                        load_only,
                                                                        pipeline_input_broadcasts,
                                                                        input_broadcast_branch_factor,
                                                                        input_broadcast_max_leaves)
        app_dir = os.path.dirname(halide_src)
        if unconstrained_io:
            fixed_io = None
        else:
            from global_buffer.io_placement import place_io_blk
            fixed_io = place_io_blk(id_to_name, app_dir)

        placement, routing, id_to_name = archipelago.pnr(self.interconnect, (netlist, bus),
                                                         load_only=load_only,
                                                         cwd=app_dir,
                                                         id_to_name=id_to_name,
                                                         fixed_pos=fixed_io,
                                                         compact=compact,
                                                         harden_flush=self.harden_flush,
                                                         pipeline_config_interval=self.pipeline_config_interval,
                                                         pes_with_packed_ponds=self.pes_with_packed_ponds)

        return placement, routing, id_to_name, instance_to_instr, netlist, bus

    def fix_pond_flush_bug(self, placement, routing):
        from collections import defaultdict

        # This is a fix for the Onyx pond hardware, in future chips we can remove this
        pond_locs = []
        for node, (x, y) in placement.items():
            if node[0] == "M" or (node in self.pes_with_packed_ponds and self.pes_with_packed_ponds[node][0] == "M"):
                pond_locs.append((x, y))

        ponds_with_routed_flush = []
        pond_to_1bit_routes = defaultdict(set)
        for _, route in routing.items():
            for segment in route:
                if "flush" in segment[-1].node_str() and "flush" in segment[-1].node_str() and (segment[-1].x, segment[-1].y) in pond_locs:
                    ponds_with_routed_flush.append((segment[-1].x, segment[-1].y))
                for node in  segment:
                    if "SB" in str(node) and node.io.value == 0 and node.width == 1 and (node.x, node.y) in pond_locs:
                        pond_to_1bit_routes[(node.x, node.y)].add((node.track, node.side.value))
                        
        bitstream = []
        for (x,y), nodes in pond_to_1bit_routes.items():
            need_fix = False
            for node in nodes:
                if node[0] == 0 and node[1] == 3 and (x,y) not in ponds_with_routed_flush:
                    need_fix = True

            if need_fix:
                found_fix = False
                for side in range(4):
                    for track in range(5):
                        if (side, track+1) not in nodes:
                            found_fix = True
                            break
                    if found_fix:
                        break

                assert found_fix, f"HW bug at flush CB {x},{y} the pond at this location will flush randomly, you will need to change the place and route result"
                source_str = ["SB", track+1, x, y, side, 0, 1]
                source_node = self.interconnect.parse_node(source_str)
                dest_str = ["PORT", "flush", x, y, 1]
                dest_node = self.interconnect.parse_node(dest_str)
                bitstream += self.interconnect.get_node_bitstream_config(source_node, dest_node)
        return bitstream

    def generate_bitstream(self, halide_src, placement, routing, id_to_name, instance_to_instr, netlist, bus,
                           compact=False):
        routing_fix = archipelago.power.reduce_switching(routing, self.interconnect,
                                                         compact=compact)
        routing.update(routing_fix)
        
        bitstream = []
        bitstream += self.interconnect.get_route_bitstream(routing)
        bitstream += self.fix_pond_flush_bug(placement, routing)
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
        delay = 0
        # also write out the meta file
        archipelago.io.dump_meta_file(
            halide_src, "design", os.path.dirname(halide_src))
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
            bitstream = compress_config_data(
                bitstream, skip_compression=skip_addr)
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


def parse_args():

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
    parser.add_argument("--amber-pond", action="store_true")
    parser.add_argument("--no-pond", action="store_true")
    parser.add_argument("--interconnect-only", action="store_true")
    parser.add_argument("--compact", action="store_true")
    parser.add_argument("--use_sim_sram", action="store_true")
    parser.add_argument("--standalone", action="store_true")
    parser.add_argument("--unconstrained-io", action="store_true")
    parser.add_argument("--dump-config-reg", action="store_true")
    parser.add_argument("--virtualize-group-size", type=int, default=4)
    parser.add_argument("--virtualize", action="store_true")
    parser.add_argument("--no-harden-flush", dest="harden_flush", action="store_false")
    parser.add_argument("--use-io-valid", action="store_true")
    parser.add_argument("--pipeline-pnr", action="store_true")
    parser.add_argument("--generate-bitstream-only", action="store_true")
    parser.add_argument("--no-input-broadcast-pipelining", action="store_true")
    parser.add_argument("--input-broadcast-branch-factor", type=int, default=4)
    parser.add_argument("--input-broadcast-max-leaves", type=int, default=16)
    parser.add_argument('--pe', type=str, default="")
    parser.add_argument('--mem-ratio', type=int, default=4)
    parser.add_argument('--num-tracks', type=int, default=5)
    parser.add_argument('--tile-layout-option', type=int, default=0)
    parser.add_argument("--rv", "--ready-valid", action="store_true", dest="ready_valid")
    parser.add_argument("--sparse-cgra", action="store_true")
    parser.add_argument("--sparse-cgra-combined", action="store_true")
    parser.add_argument("--no-pond-area-opt", action="store_true")
    parser.add_argument("--pond-area-opt-share", action="store_true")
    parser.add_argument("--no-pond-area-opt-dual-config", action="store_true")
    parser.add_argument("--sb-option", type=str, default="Imran")
    parser.add_argument("--pipeline-regs-density", nargs="+", type=int, default=None)
    parser.add_argument("--port-conn-option", nargs="+", type=int, default=None)
    parser.add_argument("--config-port-pipeline", dest="config_port_pipeline", action="store_true")
    parser.add_argument("--no-config-port-pipeline", dest="config_port_pipeline", action="store_false")
    parser.add_argument("--macro-width", type=int, default=32)
    parser.add_argument("--mem-width", type=int, default=64)
    parser.add_argument("--mem-depth", type=int, default=512)
    parser.add_argument("--mem-input-ports", type=int, default=2)
    parser.add_argument("--mem-output-ports", type=int, default=2)
    parser.add_argument("--dual-port", action="store_true")
    parser.add_argument("--rf", action="store_true")
    parser.add_argument("--dac-exp", action="store_true")

    parser.set_defaults(config_port_pipeline=True)

    args = parser.parse_args()

    # A little up-front arg processing

    if not args.interconnect_only:
        assert args.width % 2 == 0 and args.width >= 4
    if args.standalone and not args.interconnect_only:
        raise Exception("--standalone must be specified with "
                        "--interconnect-only as well")
    args.pe_fc = lassen_fc
    if args.pe:
        from peak_gen.peak_wrapper import wrapped_peak_class
        from peak_gen.arch import read_arch
        arch = read_arch(args.pe)
        args.pe_fc = wrapped_peak_class(arch, debug=True)

    from global_buffer.design.global_buffer_parameter import gen_global_buffer_params
    args.glb_params = gen_global_buffer_params(
        num_glb_tiles=args.width // 2,
        num_cgra_cols=args.width,
        # NOTE: We assume num_prr is same as num_glb_tiles
        num_prr=args.width // 2,
        glb_tile_mem_size=args.glb_tile_mem_size,
        bank_data_width=64,
        cfg_addr_width=32,
        cfg_data_width=32,
        cgra_axi_addr_width=13,
        axi_data_width=32,
        config_port_pipeline=args.config_port_pipeline,
    )

    return args

def build_verilog(args, garnet):

        garnet_circ = garnet.circuit()
        magma.compile("garnet", garnet_circ, output="coreir-verilog",
                      coreir_libs={"float_CW"},
                      passes=["rungenerators", "inline_single_instances", "clock_gate"],
                      inline=False)

        # copy in cell definitions
        from gemstone.common.mux_wrapper_aoi import AOIMuxWrapper
        files = AOIMuxWrapper.get_sv_files()
        with open("garnet.v", "a") as garnet_v:
            for filename in files:
                with open(filename) as f:
                    garnet_v.write(f.read())

        if args.sparse_cgra:
            # Cat the PE together...
            # files_cat = ['garnet.v', 'garnet_PE.v']
            lines_garnet = None
            lines_pe = None
            with open('garnet.v', 'r') as gfd:
                lines_garnet = gfd.readlines()
            with open('garnet_PE.v', 'r') as gfd:
                lines_pe = gfd.readlines()
            with open('garnet.v', 'w+') as gfd:
                gfd.writelines(lines_garnet)
                gfd.writelines(lines_pe)

        garnet.create_stub()
        if not args.interconnect_only:
            garnet_home = os.getenv('GARNET_HOME')
            if not garnet_home:
                garnet_home = os.path.dirname(os.path.abspath(__file__))

            from global_buffer.global_buffer_main import gen_param_header
            gen_param_header(top_name="global_buffer_param",
                             params=args.glb_params,
                             output_folder=os.path.join(garnet_home, "global_buffer/header"))

            gen_rdl_header(top_name="glb",
                           rdl_file=os.path.join(garnet_home, "global_buffer/systemRDL/glb.rdl"),
                           output_folder=os.path.join(garnet_home, "global_buffer/header"))
            gen_rdl_header(top_name="glc",
                           rdl_file=os.path.join(garnet_home, "global_controller/systemRDL/rdl_models/glc.rdl.final"),
                           output_folder=os.path.join(garnet_home, "global_controller/header"))

def main():
    args = parse_args()

    # BUILD GARNET
    garnet = Garnet(args)

    # FIXME OR could/should maybe do garnet.build_verilog(args), also
    # see "def place_and_route"/garnet.place_and_route(...)
    # For now, leaving it OUTSIDE the Garnet class b/c that's where
    # the code was origially (i.e. her in main())
    if args.verilog: build_verilog(args, garnet)

    if len(args.app) > 0 and len(args.input) > 0 and len(args.gold) > 0 \
            and len(args.output) > 0 and not args.virtualize:

        # place and route

        placement, routing, id_to_name, instance_to_instr, \
            netlist, bus = garnet.place_and_route(
                args.app, 
                unconstrained_io=(args.unconstrained_io or args.generate_bitstream_only),
                compact=args.compact,
                load_only=args.generate_bitstream_only,
                pipeline_input_broadcasts=not args.no_input_broadcast_pipelining,
                input_broadcast_branch_factor=args.input_broadcast_branch_factor,
                input_broadcast_max_leaves=args.input_broadcast_max_leaves)

        if args.pipeline_pnr and not args.generate_bitstream_only:
            # Calling clockwork for rescheduling pipelined app
            import subprocess
            import copy
            cwd = os.path.dirname(args.app) + "/.."
            cmd = ["make", "-C", str(cwd), "reschedule_mem"] 
            env = copy.deepcopy(os.environ)
            subprocess.check_call(
                cmd,
                env=env,
                cwd=cwd
            )

            # Wow. What? Wow.
            placement, routing, id_to_name, instance_to_instr, \
                netlist, bus = garnet.place_and_route(
                    args.app,
                    unconstrained_io=True,
                    compact=args.compact,
                    load_only=True,
                    pipeline_input_broadcasts=not args.no_input_broadcast_pipelining,
                    input_broadcast_branch_factor=args.input_broadcast_branch_factor,
                    input_broadcast_max_leaves=args.input_broadcast_max_leaves)

        bitstream, (inputs, outputs, reset, valid,
                    en, delay) = garnet.generate_bitstream(args.app, placement, routing, id_to_name, instance_to_instr,
                                                           netlist, bus, compact=args.compact)

        # write out the config file
        if len(inputs) > 1:
            if reset in inputs:
                inputs.remove(reset)
            for en_port in en:
                if en_port in inputs:
                    inputs.remove(en_port)

        from mini_mapper import get_total_cycle_from_app
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

    from passes.collateral_pass.config_register import get_interconnect_regs, get_core_registers
    if args.dump_config_reg:
        ic = garnet.interconnect
        ic_reg = get_interconnect_regs(ic)
        core_reg = get_core_registers(ic)
        with open("config.json", "w+") as f:
            json.dump(ic_reg + core_reg, f)


if __name__ == "__main__":
    main()
