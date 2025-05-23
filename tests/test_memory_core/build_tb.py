import argparse
import glob
import json
import subprocess
import sys
from gemstone.common.testers import BasicTester
from gemstone.common.configurable import ConfigurationType
from pydot import Graph
import shutil
from cgra.util import create_cgra
from memory_core.buffet_core import BuffetCore
from memory_core.core_combiner_core import CoreCombinerCore
from memory_core.crddrop_core import CrdDropCore
from memory_core.crdhold_core import CrdHoldCore
from memory_core.intersect_core import IntersectCore
from memory_core.onyx_pe_core import OnyxPECore
from memory_core.repeat_core import RepeatCore
from memory_core.repeat_signal_generator_core import RepeatSignalGeneratorCore
from memory_core.memtile_util import NetlistBuilder
from memory_core.reg_core import RegCore
from memory_core.scanner_core import ScannerCore
from memory_core.write_scanner_core import WriteScannerCore
from memory_core.stream_arbiter_core import StreamArbiterCore
from memory_core.pass_through_core import PassThroughCore
from sam.onyx.parse_dot import *
from sam.onyx.hw_nodes.hw_node import *
from sam.onyx.hw_nodes.memory_node import MemoryNode
from sam.onyx.hw_nodes.compute_node import ComputeNode
from sam.onyx.hw_nodes.glb_node import GLBNode
from sam.onyx.hw_nodes.buffet_node import BuffetNode
from sam.onyx.hw_nodes.read_scanner_node import ReadScannerNode
from sam.onyx.hw_nodes.write_scanner_node import WriteScannerNode
from sam.onyx.hw_nodes.intersect_node import IntersectNode
from sam.onyx.hw_nodes.reduce_node import ReduceNode
from sam.onyx.hw_nodes.lookup_node import LookupNode
from sam.onyx.hw_nodes.merge_node import MergeNode
from sam.onyx.hw_nodes.crdhold_node import CrdHoldNode
from sam.onyx.hw_nodes.repeat_node import RepeatNode
from sam.onyx.hw_nodes.repsiggen_node import RepSigGenNode
from sam.onyx.hw_nodes.fiberaccess_node import FiberAccessNode
from sam.onyx.hw_nodes.stream_arbiter_node import StreamArbiterNode
from sam.onyx.hw_nodes.pass_through_node import PassThroughNode
from sam.onyx.hw_nodes.locator_node import LocatorNode
import magma as m
import kratos
import _kratos
from lake.modules.buffet_like import BuffetLike
from lake.top.lake_top import LakeTop
from lake.modules.repeat import Repeat
from lake.modules.repeat_signal_generator import RepeatSignalGenerator
from lake.modules.scanner import Scanner
from lake.modules.write_scanner import WriteScanner
from lake.modules.pe import PE
from lake.modules.intersect import Intersect
from lake.modules.reg_cr import Reg
from lake.modules.counter import Counter
from lake.modules.strg_ub_vec import StrgUBVec
from lake.modules.crddrop import CrdDrop
from lake.modules.crdhold import CrdHold
from lake.modules.strg_RAM import StrgRAM
from lake.modules.stencil_valid import StencilValid
from lake.modules.stream_arbiter import StreamArbiter
from lake.modules.pass_through import PassThrough
from lake.modules.locator import Locator
import os
from canal.util import IOSide
from sam.onyx.generate_matrices import MatrixGenerator, get_tensor_from_files
import numpy
import random
from sam.sim.test.test import read_inputs
from lake.top.tech_maps import GF_Tech_Map
from lake.top.fiber_access import FiberAccess
from lake.modules.onyx_pe import OnyxPE
from lassen.sim import PE_fc
from lassen.utils import float2bfbin, bfbin2float
from peak import family
from lake.modules.scanner_pipe import ScannerPipe
import tempfile
import time
import gemstone
import torch
from sparse_app_mappings import get_tensor, get_lut_tensor
from lassen.stdlib import *
from peak.family import PyFamily
from lassen.float import *
import networkx as nx
import copy
import json
import toml
from typing import Tuple, Dict, List, Tuple


class SparseTBBuilder(m.Generator2):
    def __init__(self, nlb: NetlistBuilder = None, graph: Graph = None, bespoke=False,
                 input_dir=None, output_dir=None, local_mems=True,
                 collat_dir=None,
                 mode_map=None, real_pe=False, harden_flush=False, combined=False,
                 input_sizes=None, use_fa=False,
                 verbose=False, pnr_only=False, width=16, height=16, give_tensor=False, west_in_io_sides=False) -> None:
        assert nlb is not None or bespoke is True, "NLB is none..."
        assert graph is not None, "Graph is none..."

        self.verbose = verbose
        self.give_tensor = give_tensor

        self.nlb = nlb
        self.graph = graph
        assert mode_map is not None
        self.mode_map_ = mode_map
        self.mode_map = {}
        # Redictionary the tuples
        for k, v in self.mode_map_:
            sub_dict = {}
            for k_, v_ in v:
                sub_dict[k_] = v_
            self.mode_map[k] = sub_dict
        self.input_sizes_ = input_sizes
        self.input_sizes = {}
        # Redictionary the tuples
        for k, v in self.input_sizes_:
            self.input_sizes[k] = v
        self.core_nodes = {}
        self.glb_dones = []
        self.bespoke = bespoke
        self.core_gens = {}
        self.name_maps = {}
        self.output_dir = output_dir
        self.input_dir = input_dir
        self.local_mems = local_mems
        self.real_pe = real_pe
        self.harden_flush = harden_flush
        self.combined = combined
        self.use_fa = use_fa
        if self.use_fa:
            self.color_to_fa = {}

        self.height = height
        self.width = width

        self.input_ctr = 1 if west_in_io_sides else 0
        self.output_ctr = 2 if west_in_io_sides else 1

        self.glb_to_io_mapping = {}
        self.glb_cores = {}
        self.glb_cores_w_map = {}
        self._ctr = 0
        self.pnr_only = pnr_only
        self.collat_dir = collat_dir
        self.plus_args = []

        if bespoke is False:
            self.io = m.IO(
                clk=m.In(m.Clock),
                rst_n=m.In(m.AsyncReset),
                stall=m.In(m.Bit),
                flush=m.In(m.Bit),
                config=m.In(ConfigurationType(32, 32)),
                done=m.Out(m.Bit),
                cycle_count=m.Out(m.Bits[64])
            )

            # CGRA Path
            self.register_cores()
            self.connect_cores()

            print("Balancing SAM Graph with FIFOs")
            # ### Balance SAM graph with interconnect FIFOs #####
            new_netlist = copy.deepcopy(self.nlb._netlist)
            new_bus = copy.deepcopy(self.nlb._bus)

            # Create graph from netlist without I/O
            G = nx.DiGraph()
            remove_edges = ["data_in", "data_out", "passthrough", "stream_arb"]
            for edge, connections in new_netlist.items():
                src = connections[0][0]
                dest = connections[1][0]
                src_name = self.nlb._core_names[src]
                dest_name = self.nlb._core_names[dest]
                if not (any(edge in src_name for edge in remove_edges) or any(edge in dest_name for edge in remove_edges)):
                    G.add_edge(src, dest, name=edge)
                if "buffer_passthrough" in src_name or "buffer_passthrough" in dest_name:
                    G.add_edge(src, dest, name=edge)

            # break cycles
            cycles = list(nx.simple_cycles(G))
            while cycles:
                for cycle in cycles:
                    G.remove_edge(cycle[0], cycle[1])
                    break
                cycles = list(nx.simple_cycles(G))

            # Get first node and initialize dictionary
            first_nodes = [node for node in G.nodes if len(list(G.predecessors(node))) == 0]
            dist = {}
            parent_node = first_nodes[0]
            dist = {node: None for node in G.nodes}
            for node in first_nodes:
                dist[node] = 0

            # longest path from source to any other node
            for node in G.nodes:
                for parent_node in first_nodes:
                    if dist[node] is None:
                        all_paths = list(nx.all_simple_paths(G, source=parent_node, target=node))
                        # check all_paths is not empty list
                        if all_paths:
                            dist[node] = max(len(arr) - 1 for arr in all_paths)

            edge_add = {}

            # add to refs coming out of fiberlookups
            for node in G.nodes:
                remapping = self.nlb._core_names[node]
                if "fiber_access" in remapping and "X" not in remapping and "vals" not in remapping:
                    outgoing_edges = G.out_edges(node, data=True)
                    for edge in outgoing_edges:
                        src = edge[0]
                        dest = edge[1]
                        name = edge[2]['name']
                        if "pos" in new_netlist[name][0][1]:
                            edge_add[name] = 6

            # Compare incoming edges to add fifos
            topological_order = list(nx.topological_sort(G))
            for node in topological_order:
                incoming_edges = G.in_edges(node, data=True)
                if len(incoming_edges) > 1:
                    max_length = dist[node]
                    for edge in incoming_edges:
                        src = edge[0]
                        dest = edge[1]
                        name = edge[2]['name']
                        if dist[src] < max_length - 1:
                            # add fifos to balance + fifos added for fiberlookup refs
                            if name in edge_add:
                                prev_edge_add = edge_add[name]
                            else:
                                prev_edge_add = 0
                            edge_add[name] = 2 * (max_length - dist[src] - 1) + prev_edge_add

            # max edge_add 8
            for edge in edge_add:
                if edge_add[edge] > 8:
                    edge_add[edge] = 8
            print("Edges Added: ", edge_add)

            reg_num = 0
            edge_num = len(new_bus)
            for edge in list(new_netlist.keys()):
                src = new_netlist[edge][0]
                dest = new_netlist[edge][1]

                num_fifo = 0
                if edge in edge_add:
                    num_fifo = edge_add[edge]

                if num_fifo == 0:
                    continue

                del new_netlist[edge]
                del new_bus[edge]

                new_netlist[f"e{edge_num}"] = [src, (f"r{reg_num}", "reg")]
                new_bus[f"e{edge_num}"] = 17
                edge_num += 1

                for i in range(2 * num_fifo - 1):
                    new_netlist[f"e{edge_num}"] = [(f"r{reg_num}", "reg"), (f"r{reg_num+1}", "reg")]
                    new_bus[f"e{edge_num}"] = 17
                    edge_num += 1
                    reg_num += 1

                new_netlist[f"e{edge_num}"] = [(f"r{reg_num}", "reg"), dest]
                new_bus[f"e{edge_num}"] = 17
                edge_num += 1
                reg_num += 1

            self.nlb._netlist = new_netlist
            self.nlb._bus = new_bus

            # Now replace the io
            self.nlb.generate_placement(fixed_io=self.glb_cores)

            # Add flush connection
            if not self.harden_flush:
                flush_in = self.nlb.register_core("io_1", name="flush_in")
                self.nlb.add_connections(connections=self.nlb.emit_flush_connection(flush_in))
            self.nlb.get_route_config()
            if not self.harden_flush:
                # configure flush
                self.nlb.configure_tile(flush_in, (1, 0))
            self.configure_cores()

            # self.config = self.io.config
            # Now we have the configured CGRA...
            self.nlb.finalize_config()

            if self.pnr_only:
                return
            # Now attach global buffers based on placement...
            # Get circuit
            self.interconnect_circuit = self.nlb.get_circuit()
            self.interconnect_circuit = self.interconnect_circuit()

            # Get the initial list of inputs to interconnect and cross them off
            self.interconnect_ins = self.get_interconnect_ins()

            m.wire(self.interconnect_circuit['clk'], self.io.clk)
            m.wire(self.io.rst_n, self.interconnect_circuit['reset'])
            m.wire(self.io.stall, self.interconnect_circuit['stall'][0])
            m.wire(self.interconnect_circuit.config, self.io.config)

            if self.harden_flush:
                m.wire(self.io.flush, self.interconnect_circuit['flush'][0])
            else:
                flush_h = self.nlb.get_handle(flush_in, prefix="glb2io_1_")
                flush_tile = str(flush_h)[9:]
                flush_valid_h = f"glb2io_1_{flush_tile}_valid"

                m.wire(self.io.flush, self.interconnect_circuit[str(flush_h)][0])
                m.wire(m.Bits[1](1)[0], self.interconnect_circuit[str(flush_valid_h)])

                # Make sure to remove the flush port or it will get grounded.
                self.interconnect_ins.remove(str(flush_h))
                self.interconnect_ins.remove(str(flush_valid_h))

            # Now add the counter
            ctr = Counter(name="cycle_counter", bitwidth=64, pos_reset=True)
            ctr_magma = kratos.util.to_magma(ctr,
                                             flatten_array=False,
                                             check_multiple_driver=False,
                                             optimize_if=False,
                                             check_flip_flop_always_ff=False)

            ctr_magma_inst = ctr_magma()
            m.wire(self.io.cycle_count, ctr_magma_inst.count_out)
            m.wire(self.io.clk, ctr_magma_inst.clk)
            m.wire(self.io.rst_n, ctr_magma_inst.rst_n)
            m.wire(self.io.flush, ctr_magma_inst.flush[0])

        else:

            self.io = m.IO(
                clk=m.In(m.Clock),
                rst_n=m.In(m.AsyncReset),
                stall=m.In(m.Bit),
                flush=m.In(m.Bit),
                done=m.Out(m.Bit)
            )

            # Custom circuit path

            # First need to instantiate all the children
            self.fabric = kratos.Generator(name='fabric_proxy')
            self._u_clk = self.fabric.clock("clk")
            self._u_rst_n = self.fabric.reset("rst_n")
            self._u_flush = self.fabric.input("flush", 1)
            self._u_clk_en = self.fabric.input("stall", 1)
            self.build_fabric()
            self.wire_fabric()
            self.configure_cores()
            self.add_clk_reset()
            self.zero_alt_inputs()

            # Now we want to magma-ize this
            self.wrap_circ = kratos.util.to_magma(self.fabric,
                                                  flatten_array=False,
                                                  check_multiple_driver=False,
                                                  optimize_if=False,
                                                  check_flip_flop_always_ff=False)

            # Instance it!
            self.wrap_circ = self.wrap_circ()

            m.wire(self.io.clk, self.wrap_circ.clk)
            m.wire(self.io.rst_n, self.wrap_circ.rst_n)
            m.wire(self.io.stall, self.wrap_circ.stall[0])
            m.wire(self.io.flush, self.wrap_circ.flush[0])
            # m.wire(self.interconnect_circuit.config, self.io.config)

        self.attach_glb()

        # AND together all the dones
        if len(self.glb_dones) == 1:
            m.wire(self.io.done, self.glb_dones[0])
        else:
            tmp = self.glb_dones[0]
            for i in range(len(self.glb_dones) - 1):
                tmp = tmp & self.glb_dones[i + 1]
            m.wire(self.io.done, tmp)

        if self.bespoke is False:
            self.wire_interconnect_ins()

    def set_mode_map(self, mode_map):
        self.mode_map = mode_map

    def get_mode_map(self):
        return self.mode_map

    def enumerate_glb_in(self):
        return range(0, self.width, 2)

    def enumerate_glb_out(self):
        return range(1, self.width, 2)

    def zero_alt_inputs(self):
        '''
        Go through each child instance and zero their untouched inputs
        '''
        children = self.fabric.child_generator()
        for child in children:
            for cp in self.fabric[child].ports:
                actual_port = self.fabric[child].ports[cp]
                sourced_mask = [0 for i in range(actual_port.width)]
                if str(actual_port.port_direction) == "PortDirection.In" and str(actual_port.port_type) == "PortType.Data":
                    # If no sources, wire to 0 unless it's a ready path, then wire each bit to 1
                    if len(actual_port.sources) == 0:
                        if 'ready' in actual_port.name:
                            for i in range(actual_port.width):
                                self.fabric.wire(actual_port[i], kratos.const(1, 1))
                        else:
                            self.fabric.wire(actual_port, kratos.const(0, actual_port.width))
                    elif len(actual_port.sources) != 0 and actual_port.width != 1 and actual_port.width != 16:
                        # If there are sources and it's not 1 or 16 wide (implies they are fully driven anyway),
                        # then we need to dissect them
                        try:
                            for p in actual_port.sources:
                                for i in range(p.left.high + 1 - p.left.low):
                                    sourced_mask[i + p.left.low] = 1
                            for i in range(len(sourced_mask)):
                                if sourced_mask[i] == 0:
                                    val = 0
                                    if 'ready' in actual_port.name:
                                        val = 1
                                    self.fabric.wire(actual_port[i], kratos.const(val, 1))
                        except AttributeError:
                            if self.verbose:
                                print(f"Couldn't get bit slice, must be fully driven...{actual_port.name}")

    def add_clk_reset(self):
        '''
        Go through each child instance wire up clk, rst_n, flush, clk_en
        '''
        children = self.fabric.child_generator()
        for child in children:
            self.fabric.wire(self._u_clk, self.fabric[child].ports['clk'])
            self.fabric.wire(self._u_rst_n, self.fabric[child].ports['rst_n'])
            self.fabric.wire(self._u_flush, self.fabric[child].ports['flush'])
            self.fabric.wire(self._u_clk_en, self.fabric[child].ports['clk_en'])

    def wire_fabric(self):
        '''
        Bespoke way of connecting all the blocks in the underlying fabric
        '''
        children = self.fabric.child_generator()
        edges = self.graph.get_edges()
        for edge in edges:
            src = edge.get_source()
            dst = edge.get_destination()
            src_name = src
            dst_name = dst
            addtl_conns = self.core_nodes[src_name].connect(self.core_nodes[dst_name], edge)

            # Need to automatically add in the ready/valid interface in the bespoke case...
            if addtl_conns is not None:
                for c_b, c_l in addtl_conns.items():
                    c_l_init_length = len(c_l)
                    for i in range(c_l_init_length):
                        curr_conn = c_l[i]
                        # TODO: Handle forked connection
                        conn_spec, _ = curr_conn
                        src_c, dst_c = conn_spec
                        src_n, src_s = src_c
                        dst_n, dst_s = dst_c
                        if 'io2f' in src_s:
                            src_s = src_n

                        if 'f2io' in dst_s:
                            pass
                            # src_s = src_n
                            # dst_s = dst_n

                        # else:
                        addtl_conns[c_b].append(([(src_n, f'{src_s}_valid'), (dst_n, f'{dst_s}_valid')], 1))
                        addtl_conns[c_b].append(([(dst_n, f'{dst_s}_ready'), (src_n, f'{src_s}_ready')], 1))

            if addtl_conns is not None:
                conn_list = None
                for conn_block, cl in addtl_conns.items():
                    conn_list = cl
                for addtl_conn in conn_list:
                    # Now wire them up
                    conn_des, width = addtl_conn

                    conn_src, conn_src_prt = conn_des[0]

                    for i in range(len(conn_des) - 1):
                        # conn_dst, conn_dst_prt = conn_des[1]
                        conn_dst, conn_dst_prt = conn_des[i + 1]

                        if type(conn_src) is _kratos.Port:
                            wire_use_src = conn_src
                        else:
                            conn_src_inst = children[conn_src]
                            try:
                                wire_use_src = conn_src_inst.ports[conn_src_prt]
                            except AttributeError:
                                tk = conn_src_prt.split('_')
                                idx_str = tk[-1]
                                new_port = conn_src_prt.rstrip(f"_{idx_str}")
                                wire_use_src = conn_src_inst.ports[new_port][int(idx_str)]

                        if type(conn_dst) is _kratos.Port:
                            wire_use_dst = conn_dst
                        else:
                            conn_dst_inst = children[conn_dst]
                            try:
                                wire_use_dst = conn_dst_inst.ports[conn_dst_prt]
                            except AttributeError:
                                tk = conn_dst_prt.split('_')
                                idx_str = tk[-1]
                                new_port = conn_dst_prt.rstrip(f"_{idx_str}")
                                wire_use_dst = conn_dst_inst.ports[new_port][int(idx_str)]

                        self.fabric.wire(wire_use_src, wire_use_dst)

    def build_fabric(self):
        '''
        Go through each node and instantiate the required resources
        '''

        self.__cache_gens = {}

        for node in self.graph.get_nodes():
            kwargs = {}
            hw_node_type = node.get_attributes()['hwnode']
            new_node_type = None
            core_name = None
            core_inst = None
            new_name = node.get_attributes()['label']
            if hw_node_type == f"{HWNodeType.GLB}":
                new_node_type = GLBNode
                core_name = "glb"
            elif hw_node_type == f"{HWNodeType.Buffet}":
                new_node_type = BuffetNode
                core_name = "buffet"
                core_inst = BuffetLike(local_memory=self.local_mems)
            elif hw_node_type == f"{HWNodeType.Memory}":
                new_node_type = MemoryNode
                core_name = "memtile"
                core_inst = LakeTop()
            elif hw_node_type == f"{HWNodeType.ReadScanner}":
                new_node_type = ReadScannerNode
                core_name = "scanner"
                tensor = node.get_attributes()['tensor'].strip('"')
                kwargs = {'tensor': tensor}
                core_inst = Scanner()
            elif hw_node_type == f"{HWNodeType.WriteScanner}":
                new_node_type = WriteScannerNode
                core_name = "write_scanner"
                core_inst = WriteScanner()
            # Can't explain this but it's not a string when it's intersect?
            elif hw_node_type == f"{HWNodeType.Intersect}" or hw_node_type == HWNodeType.Intersect:
                new_node_type = IntersectNode
                core_name = "intersect"
                core_inst = Intersect(use_merger=False)
            elif hw_node_type == f"{HWNodeType.Reduce}":
                new_node_type = ReduceNode
                core_name = "regcore"
                core_inst = Reg()
            elif hw_node_type == f"{HWNodeType.Lookup}":
                new_node_type = LookupNode
                core_name = "lookup"
            elif hw_node_type == f"{HWNodeType.Merge}" or hw_node_type == HWNodeType.Merge:
                new_node_type = MergeNode
                core_name = "intersect"
                outer = node.get_attributes()['outer'].strip('"')
                inner = node.get_attributes()['inner'].strip('"')
                kwargs = {
                    "outer": outer,
                    "inner": inner
                }
                core_inst = Intersect(use_merger=True)
            elif hw_node_type == f"{HWNodeType.CrdHold}" or hw_node_type == HWNodeType.CrdHold:
                new_node_type = CrdHold
                core_name = "crdhold"
                outer = node.get_attributes()['outer'].strip('"')
                inner = node.get_attributes()['inner'].strip('"')
                kwargs = {
                    "outer": outer,
                    "inner": inner
                }
            elif hw_node_type == f"{HWNodeType.Repeat}" or hw_node_type == HWNodeType.Repeat:
                new_node_type = RepeatNode
                core_name = "repeat"
                core_inst = Repeat()
            elif hw_node_type == f"{HWNodeType.Compute}" or hw_node_type == HWNodeType.Compute:
                new_node_type = ComputeNode
                core_name = "fake_pe"
                core_inst = PE()
            elif hw_node_type == f"{HWNodeType.RepSigGen}" or hw_node_type == HWNodeType.RepSigGen:
                new_node_type = RepSigGenNode
                core_name = "repeat_signal_generator"
                core_inst = RepeatSignalGenerator()
            elif hw_node_type == f"{HWNodeType.StreamArbiter}" or hw_node_type == HWNodeType.StreamArbiter:
                new_node_type = StreamArbiterNode
                core_name = "stream_arbiter"
                core_inst = StreamArbiter()
            elif hw_node_type == f"{HWNodeType.PassThrough}" or hw_node_type == HWNodeType.PassThrough:
                new_node_type = PassThroughNode
                core_name = "pass_through"
                core_inst = PassThrough()
            elif hw_node_type == f"{HWNodeType.Locator}":
                new_node_type = LocatorNode
                core_name = "locator"
                locate_lvl = int(node.get_attributes()['lvl'].strip('"'))
                locate_dim_size = int(node.get_attributes()['dim_size'].strip('"'))
                kwargs = {
                    "locate_lvl": locate_lvl,
                    "locate_dim_size": locate_dim_size
                }
                core_inst = Locator()
            else:
                raise NotImplementedError(f"{hw_node_type} not supported....")

            assert new_node_type is not None
            assert core_name != ""
            if new_node_type == GLBNode:
                conn_id = self.get_next_seq()
                # Have to handle the GLB nodes slightly differently
                # Instead of directly registering a core, we are going to register the io,
                # connect them to the appropriate block, then instantiate and wire a
                # systemverilog wrapper of the simulation level transactions for GLB
                if node.get_attributes()['type'].strip('"') == 'fiberlookup':
                    # GLB write wants a data input, ready, valid
                    glb_name = "GLB_TO_CGRA"
                    direction = "write"
                    num_blocks = 1
                    file_number = 0
                    data = self.fabric.input(f'data_in_{conn_id}', 17)
                    ready = self.fabric.output(f'data_in_{conn_id}_ready', 1)
                    valid = self.fabric.input(f'data_in_{conn_id}_valid', 1)
                    tx_size = 7

                    if node.get_attributes()['mode'].strip('"') == 1 or node.get_attributes()['mode'].strip('"') == '1':
                        file_number = 1
                        tx_size = 12
                    # glb_writer = m.define_from_verilog_file()
                elif node.get_attributes()['type'].strip('"') == 'fiberwrite':
                    # GLB read wants a data output, ready, valid
                    direction = "read"
                    glb_name = "CGRA_TO_GLB"
                    data = self.fabric.output(f'data_out_{conn_id}', 17)
                    ready = self.fabric.input(f'data_out_{conn_id}_ready', 1)
                    valid = self.fabric.output(f'data_out_{conn_id}_valid', 1)
                    if 'vals' in node.get_attributes()['mode'].strip('"') or 'vals' in node.get_attributes()['format'].strip('"'):
                        num_blocks = 1
                    else:
                        num_blocks = 2
                    tx_size = 1
                elif node.get_attributes()['type'].strip('"') == 'arrayvals':
                    # GLB write wants a data input, ready, valid
                    glb_name = "GLB_TO_CGRA"
                    data = self.fabric.input(f'data_in_{conn_id}', 17)
                    ready = self.fabric.output(f'data_in_{conn_id}_ready', 1)
                    valid = self.fabric.input(f'data_in_{conn_id}_valid', 1)
                    direction = "write"
                    num_blocks = 1
                    tx_size = 7
                    file_number = 2
                else:
                    raise NotImplementedError

                glb_tensor = node.get_attributes()['tensor'].strip('"')
                if 'arrayvals' in node.get_attributes()['type'].strip('"'):
                    glb_mode = 'vals'
                else:
                    glb_mode = node.get_attributes()['mode'].strip('"')

                self.core_nodes[node.get_name()] = GLBNode(name=glb_name,
                                                           data=data,
                                                           valid=valid,
                                                           ready=ready,
                                                           direction=direction,
                                                           num_blocks=num_blocks,
                                                           file_number=file_number,
                                                           tx_size=tx_size,
                                                           IO_id=self.get_next_seq(),
                                                           bespoke=True,
                                                           tensor=glb_tensor,
                                                           mode=glb_mode)
            else:
                # reg_ret = self.nlb.register_core(core_tag, flushable=True, name=new_name)
                inst_name = f"{core_name}_{self.get_next_seq()}"
                self.name_maps[inst_name] = node.get_attributes()['label'].strip('"')
                self.core_nodes[node.get_name()] = new_node_type(name=inst_name, **kwargs)
                # Need to flatten first - but not if memory tile because of some bad code
                if new_node_type == MemoryNode:
                    self.core_gens[node.get_name()] = core_inst.dut
                    self.fabric.add_child(inst_name, core_inst.dut)
                else:
                    self.core_gens[node.get_name()] = core_inst
                    flattened = _kratos.create_wrapper_flatten(core_inst.internal_generator, f"{core_inst.name}_flat")
                    flattened_gen = kratos.Generator(f"{core_inst.name}_flat", internal_generator=flattened)
                    self.fabric.add_child(inst_name, flattened_gen)

    def get_next_seq(self):
        tmp = self._ctr
        self._ctr += 1
        return tmp

    def get_interconnect_ins(self):
        '''
        Need to ascertain all inputs to interconnect so we can later make sure they are driven
        Want to do this early so we can delete references while processing the glb attachments
        '''
        in_list = []

        all_ports = self.interconnect_circuit.interface
        for port in all_ports:
            if 'glb2io' in port and 'ready' not in port:
                in_list.append(port)
            elif 'io2glb' in port and 'ready' in port:
                in_list.append(port)

        return in_list

    def wire_interconnect_ins(self):
        '''
        Here we are going to wire all of the relevant interconnect inputs to 0
        '''
        for ic_in in self.interconnect_ins:
            # Get width from name
            if 'ready' not in ic_in and 'valid' not in ic_in:
                width = int(ic_in.split("_")[1])
                m.wire(self.interconnect_circuit[ic_in], m.Bits[width](0))
            else:
                width = 1
                m.wire(self.interconnect_circuit[ic_in], m.Bits[width](0)[0])

    def attach_glb(self):

        # In this case, we should just hook up GLB nodes to every single one...
        # That way we generate a single verilog, we can swap in the plusargs
        if not self.bespoke:

            print("NON BESPOKE BULK GLB")

            for glb_in in self.enumerate_glb_in():

                print(f"GLB_BULK_{glb_in}")

                if (glb_in, 0) in self.glb_cores_w_map:
                    use_param = True
                    node_ = self.glb_cores_w_map[(glb_in, 0)]
                    glb_data = node_.get_data()
                    glb_ready = node_.get_ready()
                    glb_valid = node_.get_valid()
                    glb_num_blocks = node_.get_num_blocks()
                    glb_file_number = node_.get_file_number()
                    glb_tx_size = node_.get_tx_size()

                    glb_tensor = node_.get_tensor()
                    print(glb_tensor)
                    glb_mode_ = node_.get_mode()
                    print(glb_mode_)
                    print(self.mode_map)
                    if 'vals' not in glb_mode_:
                        glb_mode_ = int(glb_mode_)
                        glb_mode = glb_mode_
                    else:
                        glb_mode = glb_mode_
                    # Get the handle for these pins, then instantiate glb
                    print(glb_mode)
                else:
                    use_param = False

                # data_h = self.nlb.get_handle(glb_data, prefix="glb2io_17_")
                data_h = f"glb2io_17_X{glb_in:02X}_Y00"
                suffix = str(data_h)[10:]
                ready_h = f"glb2io_17_{suffix}_ready"
                valid_h = f"glb2io_17_{suffix}_valid"
                print(data_h)
                print(suffix)

                # Get rid of these signals from leftover inputs...
                self.interconnect_ins.remove(str(data_h))
                self.interconnect_ins.remove(str(valid_h))

                data_h = self.interconnect_circuit[str(data_h)]
                ready_h = self.interconnect_circuit[str(ready_h)]
                valid_h = self.interconnect_circuit[str(valid_h)]

                class _Definition(m.Generator2):
                    def __init__(self, TX_SIZE, FILE_NAME, ID_no, LOCATION) -> None:
                        # super().__init__()
                        self.name = f"glb_write_wrapper_{TX_SIZE}_{ID_no}"
                        self.io = m.IO(**{
                            "clk": m.In(m.Clock),
                            "rst_n": m.In(m.AsyncReset),
                            "data": m.Out(m.Bits[17]),
                            "ready": m.In(m.Bit),
                            "valid": m.Out(m.Bit),
                            "done": m.Out(m.Bit),
                            "flush": m.In(m.Bit)
                        })
                        self.verilog = f"""
                glb_write  #(.TX_SIZE({TX_SIZE}), .FILE_NAME({FILE_NAME}), .LOCATION({LOCATION}))
                test_glb_inst
                (
                    .clk(clk),
                    .rst_n(rst_n),
                    .data(data),
                    .ready(ready),
                    .valid(valid),
                    .done(done),
                    .flush(flush)
                );
                """

                if use_param:
                    file_full = f"{self.input_dir}/tensor_{glb_tensor}_mode_{glb_mode}_{glb_file_number}"
                    # Get tx size now
                    if not node_.get_format() == "dense":
                        try:
                            with open(file_full, "r") as ff:
                                glb_tx_size = len(ff.readlines())
                        except:
                            glb_tx_size = 0
                    else:
                        glb_tx_size = 0

                    file_full = f"\"{file_full}\""
                else:
                    file_full = ""
                    glb_tx_size = 0

                location_str = f"\"X{glb_in:02X}_Y00\""
                test_glb = _Definition(TX_SIZE=glb_tx_size, FILE_NAME=file_full,
                                       ID_no=self.get_next_seq(),
                                       LOCATION=location_str)()

                m.wire(test_glb['data'], data_h)
                m.wire(ready_h, test_glb['ready'])
                m.wire(test_glb['valid'], valid_h)
                m.wire(test_glb.clk, self.io.clk)
                m.wire(test_glb.rst_n, self.io.rst_n)
                m.wire(test_glb.flush, self.io.flush)

                self.glb_dones.append(test_glb.done)

            for glb_out in self.enumerate_glb_out():

                if (glb_out, 0) in self.glb_cores_w_map:
                    use_param = True
                    node_ = self.glb_cores_w_map[(glb_out, 0)]
                    glb_data = node_.get_data()
                    glb_ready = node_.get_ready()
                    glb_valid = node_.get_valid()
                    glb_num_blocks = node_.get_num_blocks()
                    glb_file_number = node_.get_file_number()
                    glb_tx_size = node_.get_tx_size()

                    glb_tensor = node_.get_tensor()
                    glb_mode_ = node_.get_mode()
                    if 'vals' not in glb_mode_:
                        glb_mode_ = int(glb_mode_)
                        glb_mode = glb_mode_
                    else:
                        glb_mode = glb_mode_
                else:
                    use_param = False

                data_h = f"io2glb_17_X{glb_out:02X}_Y00"
                suffix = str(data_h)[10:]

                ready_h = f"io2glb_17_{suffix}_ready"
                valid_h = f"io2glb_17_{suffix}_valid"

                # Get rid of this signal from leftover inputs...
                self.interconnect_ins.remove(str(ready_h))

                data_h = self.interconnect_circuit[str(data_h)]
                ready_h = self.interconnect_circuit[str(ready_h)]
                valid_h = self.interconnect_circuit[str(valid_h)]

                class _Definition(m.Generator2):
                    def __init__(self, NUM_BLOCKS, FILE_NAME1, FILE_NAME2, ID_no, LOCATION) -> None:
                        self.name = f"glb_read_wrapper_{NUM_BLOCKS}_{ID_no}"
                        self.io = m.IO(**{
                            "clk": m.In(m.Clock),
                            "rst_n": m.In(m.AsyncReset),
                            "data": m.In(m.Bits[17]),
                            "ready": m.Out(m.Bit),
                            "valid": m.In(m.Bit),
                            "done": m.Out(m.Bit),
                            "flush": m.In(m.Bit)
                        })

                        self.verilog = f"""
                glb_read #(.NUM_BLOCKS({NUM_BLOCKS}), .FILE_NAME1({FILE_NAME1}), .FILE_NAME2({FILE_NAME2}), .LOCATION({LOCATION}))
                test_glb_inst
                (
                    .clk(clk),
                    .rst_n(rst_n),
                    .data(data),
                    .ready(ready),
                    .valid(valid),
                    .done(done),
                    .flush(flush)
                );
                """

                ID_no = self.get_next_seq()

                if use_param:

                    if str(glb_mode) == "vals":
                        f1 = f"\"{self.output_dir}/tensor_X_mode_{glb_mode}_{glb_file_number}\""
                        f2 = f1
                    elif node_.get_format() == 'vals':
                        f1 = f"\"{self.output_dir}/tensor_X_mode_{glb_mode}_{glb_file_number}\""
                        f2 = f1
                    else:
                        f1 = f"\"{self.output_dir}/tensor_X_mode_{glb_mode}_seg_{glb_file_number}\""
                        f2 = f"\"{self.output_dir}/tensor_X_mode_{glb_mode}_crd_{glb_file_number}\""

                else:

                    glb_num_blocks = 0
                    f1 = ""
                    f2 = ""

                location_str = f"\"X{glb_out:02X}_Y00\""
                test_glb = _Definition(NUM_BLOCKS=glb_num_blocks, FILE_NAME1=f1,
                                       FILE_NAME2=f2, ID_no=ID_no,
                                       LOCATION=location_str)()

                m.wire(data_h, test_glb['data'])
                m.wire(test_glb['ready'], ready_h)
                m.wire(valid_h, test_glb['valid'])
                m.wire(test_glb.clk, self.io.clk)
                m.wire(test_glb.rst_n, self.io.rst_n)
                m.wire(test_glb.flush, self.io.flush)

                self.glb_dones.append(test_glb.done)

            return

        # glb_nodes = [node for node in self.core_nodes.values() if type(node) == GLBNode]
        glb_nodes = [node for node in self.core_nodes.values() if isinstance(node, GLBNode)]
        for node in glb_nodes:
            # Now we can realize and connect the glb nodes based on the placement
            glb_data = node.get_data()
            glb_ready = node.get_ready()
            glb_valid = node.get_valid()
            glb_num_blocks = node.get_num_blocks()
            glb_file_number = node.get_file_number()
            glb_tx_size = node.get_tx_size()

            glb_tensor = node.get_tensor()
            glb_mode_ = node.get_mode()
            if 'vals' not in glb_mode_:
                glb_mode_ = int(glb_mode_)
                glb_mode = glb_mode_
            else:
                glb_mode = glb_mode_
            # Get the handle for these pins, then instantiate glb
            glb_dir = node.get_direction()
            if glb_dir == 'write':

                # In the bespoke case we can use the data ports
                if self.bespoke:
                    data_h = self.wrap_circ[glb_data.name]
                    ready_h = self.wrap_circ[glb_ready.name]
                    valid_h = self.wrap_circ[glb_valid.name]
                else:
                    data_h = self.nlb.get_handle(glb_data, prefix="glb2io_17_")
                    suffix = str(data_h)[10:]
                    ready_h = f"glb2io_17_{suffix}_ready"
                    valid_h = f"glb2io_17_{suffix}_valid"

                    # Get rid of these signals from leftover inputs...
                    self.interconnect_ins.remove(str(data_h))
                    self.interconnect_ins.remove(str(valid_h))

                    data_h = self.interconnect_circuit[str(data_h)]
                    ready_h = self.interconnect_circuit[str(ready_h)]
                    valid_h = self.interconnect_circuit[str(valid_h)]

                class _Definition(m.Generator2):
                    def __init__(self, TX_SIZE, FILE_NAME, ID_no) -> None:
                        self.name = f"glb_write_wrapper_{TX_SIZE}_{ID_no}"
                        self.io = m.IO(**{
                            "clk": m.In(m.Clock),
                            "rst_n": m.In(m.AsyncReset),
                            "data": m.Out(m.Bits[17]),
                            "ready": m.In(m.Bit),
                            "valid": m.Out(m.Bit),
                            "done": m.Out(m.Bit),
                            "flush": m.In(m.Bit)
                        })
                        self.verilog = f"""
                glb_write  #(.TX_SIZE({TX_SIZE}), .FILE_NAME({FILE_NAME}))
                test_glb_inst
                (
                    .clk(clk),
                    .rst_n(rst_n),
                    .data(data),
                    .ready(ready),
                    .valid(valid),
                    .done(done),
                    .flush(flush)
                );
                """

                file_full = f"{self.input_dir}/tensor_{glb_tensor}_mode_{glb_mode}"
                # Get tx size now
                if not node.get_format() == "dense":
                    try:
                        with open(file_full, "r") as ff:
                            glb_tx_size = len(ff.readlines())
                    except:
                        glb_tx_size = 0
                else:
                    glb_tx_size = 0

                file_full = f"\"{file_full}\""
                test_glb = _Definition(TX_SIZE=glb_tx_size, FILE_NAME=file_full, ID_no=self.get_next_seq())()

                m.wire(test_glb['data'], data_h)
                m.wire(ready_h, test_glb['ready'])
                m.wire(test_glb['valid'], valid_h)
                m.wire(test_glb.clk, self.io.clk)
                m.wire(test_glb.rst_n, self.io.rst_n)
                m.wire(test_glb.flush, self.io.flush)

            elif glb_dir == 'read':

                if self.bespoke:
                    data_h = self.wrap_circ[glb_data.name]
                    ready_h = self.wrap_circ[glb_ready.name]
                    valid_h = self.wrap_circ[glb_valid.name]
                else:
                    data_h = self.nlb.get_handle(glb_data, prefix="io2glb_17_")
                    suffix = str(data_h)[10:]
                    ready_h = f"io2glb_17_{suffix}_ready"
                    valid_h = f"io2glb_17_{suffix}_valid"

                    # Get rid of this signal from leftover inputs...
                    self.interconnect_ins.remove(str(ready_h))

                    data_h = self.interconnect_circuit[str(data_h)]
                    ready_h = self.interconnect_circuit[str(ready_h)]
                    valid_h = self.interconnect_circuit[str(valid_h)]

                class _Definition(m.Generator2):
                    def __init__(self, NUM_BLOCKS, FILE_NAME1, FILE_NAME2, ID_no) -> None:
                        # super().__init__()
                        self.name = f"glb_read_wrapper_{NUM_BLOCKS}_{ID_no}"
                        self.io = m.IO(**{
                            "clk": m.In(m.Clock),
                            "rst_n": m.In(m.AsyncReset),
                            "data": m.In(m.Bits[17]),
                            "ready": m.Out(m.Bit),
                            "valid": m.In(m.Bit),
                            "done": m.Out(m.Bit),
                            "flush": m.In(m.Bit)
                        })

                        self.verilog = f"""
                glb_read #(.NUM_BLOCKS({NUM_BLOCKS}), .FILE_NAME1({FILE_NAME1}), .FILE_NAME2({FILE_NAME2}))
                test_glb_inst
                (
                    .clk(clk),
                    .rst_n(rst_n),
                    .data(data),
                    .ready(ready),
                    .valid(valid),
                    .done(done),
                    .flush(flush)
                );
                """

                ID_no = self.get_next_seq()

                if str(glb_mode) == "vals":
                    f1 = f"\"{self.output_dir}/tensor_X_mode_{glb_mode}\""
                    f2 = f1
                elif node.get_format() == 'vals':
                    f1 = f"\"{self.output_dir}/tensor_X_mode_{glb_mode}\""
                    f2 = f1
                else:
                    f1 = f"\"{self.output_dir}/tensor_X_mode_{glb_mode}_seg\""
                    f2 = f"\"{self.output_dir}/tensor_X_mode_{glb_mode}_crd\""

                test_glb = _Definition(NUM_BLOCKS=glb_num_blocks, FILE_NAME1=f1, FILE_NAME2=f2, ID_no=ID_no)()

                m.wire(data_h, test_glb['data'])
                m.wire(test_glb['ready'], ready_h)
                m.wire(valid_h, test_glb['valid'])
                m.wire(test_glb.clk, self.io.clk)
                m.wire(test_glb.rst_n, self.io.rst_n)
                m.wire(test_glb.flush, self.io.flush)
            else:
                raise NotImplementedError(f"glb_dir was {glb_dir}")

            self.glb_dones.append(test_glb.done)

    def register_cores(self):
        '''
        Go through each core and register it, also add it to dict of core nodes
        '''

        for node in self.graph.get_nodes():
            kwargs = {}
            hw_node_type = node.get_attributes()['hwnode']
            new_node_type = None
            core_tag = None
            new_name = node.get_attributes()['label']
            if hw_node_type == f"{HWNodeType.GLB}":
                new_node_type = GLBNode
                core_tag = "glb"
            elif hw_node_type == f"{HWNodeType.Buffet}":
                new_node_type = BuffetNode
                core_tag = "buffet"
            elif hw_node_type == f"{HWNodeType.Memory}":
                new_node_type = MemoryNode
                core_tag = "memtile"
            elif hw_node_type == f"{HWNodeType.ReadScanner}":
                new_node_type = ReadScannerNode
                core_tag = "read_scanner"
                type = node.get_attributes()['type'].strip('"')
                tensor = node.get_attributes()['tensor'].strip('"')

                # Mode and dim size would only be set by fiberlookup,
                # as a vals lookup is a different type, and otherwise
                # it is the complementary rs to a ws
                if type == 'fiberlookup':
                    mode = node.get_attributes()['mode'].strip('"')
                    # May not need to use/have dim size info for a certain tensor
                    if tensor in self.input_sizes:
                        dim_size = self.input_sizes[tensor][int(mode)]
                    else:
                        dim_size = None
                    if 'vector_reduce_mode' in node.get_attributes():
                        is_in_vr_mode = node.get_attributes()['vector_reduce_mode'].strip('"')
                        if is_in_vr_mode == "true":
                            index = None
                        else:
                            index = node.get_attributes()['index'].strip('"')
                    else:
                        index = node.get_attributes()['index'].strip('"')
                    format = node.get_attributes()['format'].strip('"')
                else:
                    mode = None
                    dim_size = None
                    index = None
                    format = None

                kwargs = {'tensor': tensor,
                          'mode': mode,
                          'dim_size': dim_size,
                          'index': index,
                          'format': format}
            elif hw_node_type == f"{HWNodeType.WriteScanner}":
                new_node_type = WriteScannerNode
                core_tag = "write_scanner"
            # Can't explain this but it's not a string when it's intersect?
            elif hw_node_type == f"{HWNodeType.Intersect}" or hw_node_type == HWNodeType.Intersect:
                new_node_type = IntersectNode
                core_tag = "intersect"
                edges_to_isect = [edge for edge in self.graph.get_edges() if edge.get_destination() == node.get_name()]
                edges_to_isect_crd = [edge for edge in edges_to_isect if edge.get_attributes()['type'].strip('"') == "crd"]
                conn_to_tensor = {}
                for idx_, edge in enumerate(edges_to_isect_crd):
                    conn_to_tensor[idx_] = edge.get_attributes()['comment'].strip('"').split('-')[1]
                kwargs = {'conn_to_tensor': conn_to_tensor}

            elif hw_node_type == f"{HWNodeType.Reduce}":
                new_node_type = ReduceNode
                # Both pe and reduce sit in reduce_pe_cluster
                # Give them the same core tag so reduce_pe_cluster.get_bitstream is called
                # for both pe and reduce
                core_tag = "alu"
            elif hw_node_type == f"{HWNodeType.Lookup}":
                new_node_type = LookupNode
                core_tag = "lookup"
            elif hw_node_type == f"{HWNodeType.Merge}" or hw_node_type == HWNodeType.Merge:
                new_node_type = MergeNode
                core_tag = "crddrop"
                outer = node.get_attributes()['outer'].strip('"')
                inner = node.get_attributes()['inner'].strip('"')
                if 'mode' in node.get_attributes():
                    mode = int(node.get_attributes()['mode'].strip('"'))
                else:
                    # if not specified, mode is set to crddrop mode
                    mode = 1
                kwargs = {
                    "outer": outer,
                    "inner": inner,
                    "mode": mode
                }
            elif hw_node_type == f"{HWNodeType.CrdHold}" or hw_node_type == HWNodeType.CrdHold:
                new_node_type = CrdHoldNode
                core_tag = "crdhold"
                outer = node.get_attributes()['outer'].strip('"')
                inner = node.get_attributes()['inner'].strip('"')
                kwargs = {
                    "outer": outer,
                    "inner": inner
                }
            elif hw_node_type == f"{HWNodeType.Repeat}" or hw_node_type == HWNodeType.Repeat:
                new_node_type = RepeatNode
                core_tag = "repeat"
            elif hw_node_type == f"{HWNodeType.Compute}" or hw_node_type == HWNodeType.Compute:
                new_node_type = ComputeNode
                # core_tag = "fake_pe"
                core_tag = "alu"
                if "is_mapped_from_complex_op" in node.get_attributes():
                    assert 'original_complex_op_id' in node.get_attributes()
                    is_mapped_from_complex_op = node.get_attributes()["is_mapped_from_complex_op"]
                    original_complex_op_id = node.get_attributes()["original_complex_op_id"].strip('"')
                else:
                    is_mapped_from_complex_op = False
                    original_complex_op_id = None
                kwargs = {
                    "op": node.get_attributes()['label'].strip('"'),
                    "sam_graph_node_id": node.get_name(),
                    "mapped_coreir_dir": self.collat_dir,
                    "is_mapped_from_complex_op": is_mapped_from_complex_op,
                    "original_complex_op_id": original_complex_op_id
                }
            elif hw_node_type == f"{HWNodeType.RepSigGen}" or hw_node_type == HWNodeType.RepSigGen:
                new_node_type = RepSigGenNode
                core_tag = "rsg"
            elif hw_node_type == f"{HWNodeType.StreamArbiter}" or hw_node_type == HWNodeType.StreamArbiter:
                new_node_type = StreamArbiterNode
                core_tag = "stream_arbiter"
            elif hw_node_type == f"{HWNodeType.PassThrough}" or hw_node_type == HWNodeType.PassThrough:
                new_node_type = PassThroughNode
                core_tag = "pass_through"
                edges_to_pass_through = [edge for edge in self.graph.get_edges() if edge.get_destination() == node.get_name()]
                assert len(edges_to_pass_through) == 1
                edge = edges_to_pass_through[0]
                # from ref need to pass conn_to_tensor, if it has tensor name ('-' in comment), ex. in-C
                if 'comment' in edge.get_attributes() and '-' in edge.get_attributes()['comment'].strip('"'):
                    conn_to_tensor = {}
                    conn_to_tensor[0] = edge.get_attributes()['comment'].strip('"').split('-')[1]
                    kwargs = {'conn_to_tensor': conn_to_tensor}
                else:
                    kwargs = {}
            elif hw_node_type == f"{HWNodeType.Locator}":
                new_node_type = LocatorNode
                core_tag = "locator"
                locate_lvl = int(node.get_attributes()['lvl'].strip('"'))
                locate_dim_size = int(node.get_attributes()['dim_size'].strip('"'))
                kwargs = {
                    "locate_lvl": locate_lvl,
                    "locate_dim_size": locate_dim_size
                }
            else:
                raise NotImplementedError(f"{hw_node_type} not supported....")

            assert new_node_type is not None
            assert core_tag != ""
            if new_node_type == GLBNode:
                glb_tensor_ = node.get_attributes()['tensor'].strip('"')
                glb_type_ = node.get_attributes()['type'].strip('"')
                if 'arrayvals' in glb_type_:
                    glb_mode_ = 'vals'
                else:
                    glb_mode_ = node.get_attributes()['mode'].strip('"')
                if 'file_id' in node.get_attributes():
                    file_number = node.get_attributes()['file_id']
                else:
                    file_number = None
                # Have to handle the GLB nodes slightly differently
                # Instead of directly registering a core, we are going to register the io,
                # connect them to the appropriate block, then instantiate and wire a
                # systemverilog wrapper of the simulation level transactions for GLB
                if glb_type_ == 'fiberlookup':
                    glb_name = "GLB_TO_CGRA"
                    data = self.nlb.register_core("io_16", name=f"data_in_{glb_tensor_}_{glb_mode_}")
                    direction = "write"
                    num_blocks = 1
                    tx_size = 7
                    seg_mode = 0  # placeholder
                    if node.get_attributes()['mode'].strip('"') == 1 or node.get_attributes()['mode'].strip('"') == '1':
                        tx_size = 12
                elif glb_type_ == 'fiberwrite' or glb_type_ == 'spaccumulator':
                    data = self.nlb.register_core("io_16", name=f"data_out_{glb_tensor_}_{glb_mode_}")
                    direction = "read"
                    glb_name = "CGRA_TO_GLB"
                    num_blocks = 1
                    if 'vals' in glb_mode_ or 'vals' in node.get_attributes()['format'].strip('"'):
                        seg_mode = 0
                    else:
                        seg_mode = 1
                    tx_size = 1
                elif glb_type_ == 'arrayvals':
                    glb_name = "GLB_TO_CGRA"
                    data = self.nlb.register_core("io_16", name=f"data_in_{glb_tensor_}_{glb_mode_}")
                    direction = "write"
                    num_blocks = 1
                    tx_size = 7
                    seg_mode = 0  # placeholder
                else:
                    raise NotImplementedError

                # Set tensor and mode for writing
                glb_tensor = node.get_attributes()['tensor'].strip('"')
                if 'arrayvals' in node.get_attributes()['type'].strip('"'):
                    glb_mode = 'vals'
                else:
                    glb_mode = node.get_attributes()['mode'].strip('"')

                glb_format = node.get_attributes()['format'].strip('"') if 'format' in node.get_attributes().keys() else None

                glb_node_use = GLBNode(name=data,
                                       data=data,
                                       valid=None,
                                       # valid=valid,
                                       ready=None,
                                       # ready=ready,
                                       direction=direction,
                                       num_blocks=num_blocks,
                                       seg_mode=seg_mode,
                                       file_number=file_number,
                                       tx_size=tx_size,
                                       tensor=glb_tensor,
                                       mode=glb_mode,
                                       format=glb_format)
                self.core_nodes[node.get_name()] = glb_node_use

                self.glb_to_io_mapping[data] = (glb_tensor, glb_mode, direction, num_blocks, seg_mode, file_number)

                glb_mode_ = glb_mode
                if 'vals' not in glb_mode_:
                    glb_mode_ = int(glb_mode_)
                    glb_mode__ = glb_mode_
                else:
                    glb_mode__ = glb_mode_

                if direction == "write":
                    self.glb_cores[data] = (self.input_ctr, 0)
                    self.glb_cores_w_map[(self.input_ctr, 0)] = glb_node_use
                    file_full = f"{{}}/tensor_{glb_tensor}_mode_{glb_mode__}_{file_number}"

                    file_full = f"\"{file_full}\""
                    self.plus_args.append((f"+X{self.input_ctr:02X}_Y00_FILE_NAME={file_full}\n", 'input'))
                    self.plus_args.append(f"+X{self.input_ctr:02X}_Y00_ENABLED=1\n")

                    self.input_ctr += 2

                else:
                    self.glb_cores[data] = (self.output_ctr, 0)
                    self.glb_cores_w_map[(self.output_ctr, 0)] = glb_node_use

                    if str(glb_mode__) == "vals":
                        f1 = f"\"{{}}/tensor_X_mode_{glb_mode__}_{file_number}\""
                        f2 = f1
                    elif glb_format == 'vals':
                        f1 = f"\"{{}}/tensor_X_mode_{glb_mode__}_{file_number}\""
                        f2 = f1
                    else:
                        f1 = f"\"{{}}/tensor_X_mode_{glb_mode__}_seg_{file_number}\""
                        f2 = f"\"{{}}/tensor_X_mode_{glb_mode__}_crd_{file_number}\""

                    self.plus_args.append((f"+X{self.output_ctr:02X}_Y00_F1={f1}\n", 'output'))
                    self.plus_args.append((f"+X{self.output_ctr:02X}_Y00_F2={f2}\n", 'output'))
                    self.plus_args.append(f"+X{self.output_ctr:02X}_Y00_NUM_BLOCKS={num_blocks}\n")
                    self.plus_args.append(f"+X{self.output_ctr:02X}_Y00_ENABLED=1\n")

                    self.output_ctr += 2

            else:
                # Here we can deal with FA
                if self.use_fa and (core_tag == "read_scanner" or core_tag == "write_scanner" or core_tag == "buffet"):
                    # We want to map these cores to the same FA if we can
                    node_attr = node.get_attributes()
                    if 'vector_reduce_mode' not in node_attr:
                        tensor = node_attr['tensor'].strip('"')
                        stream_id = str(node_attr['stream_id'])
                        if 'mode' in node_attr:
                            mode = node_attr['mode'].strip('"')
                        else:
                            mode = 'vals'
                        color = tensor + mode + stream_id
                    else:
                        color = node_attr['fa_color']
                    if color not in self.color_to_fa:
                        reg_ret = self.nlb.register_core("fiber_access", flushable=True, name=f'fiber_access_{color}')
                        self.color_to_fa[color] = FiberAccessNode(name=reg_ret)

                    # Map the core nodes all to the same fiber access
                    # This will force all the connections/configurations to go through this object
                    self.core_nodes[node.get_name()] = (self.color_to_fa[color], core_tag)

                    if core_tag == "read_scanner":
                        self.color_to_fa[color].set_read_scanner(new_node_type(name=reg_ret, **kwargs))
                    elif core_tag == "write_scanner":
                        self.color_to_fa[color].set_write_scanner(new_node_type(name=reg_ret, **kwargs))
                    elif core_tag == "buffet":
                        self.color_to_fa[color].set_buffet(new_node_type(name=reg_ret, **kwargs))

                else:
                    reg_ret = self.nlb.register_core(core_tag, flushable=True, name=new_name)
                    self.core_nodes[node.get_name()] = new_node_type(name=reg_ret, **kwargs)

    def get_glb_mapping(self):
        return self.glb_to_io_mapping

    def find_node_by_name(self, name):
        for node in self.graph.get_nodes():
            if node.get_name() == name:
                return node
        assert False

    def connect_cores(self):
        '''
        Iterate through the edges of the graph and connect each core up
        '''
        edges = self.graph.get_edges()
        for edge in edges:
            src_name = edge.get_source()
            dst_name = edge.get_destination()
            # print(f"Connecting {src_name} to {dst_name}")

            if self.use_fa:
                # If the nodes have the same fa_color, don't connect them explicitly
                kwargs = {}
                src_node = self.find_node_by_name(src_name)
                dst_node = self.find_node_by_name(dst_name)
                src_attr = src_node.get_attributes()
                dst_attr = dst_node.get_attributes()
                if 'fa_color' in src_attr and 'fa_color' in dst_attr:
                    if src_attr['fa_color'] == dst_attr['fa_color']:
                        continue

                if 'fa_color' in src_attr:
                    _s, flavor_this = self.core_nodes[src_name]
                    kwargs['flavor_this'] = flavor_this
                    src_core_node = _s
                else:
                    src_core_node = self.core_nodes[src_name]

                if 'fa_color' in dst_attr:
                    _d, flavor_that = self.core_nodes[dst_name]
                    kwargs['flavor_that'] = flavor_that
                    dst_core_node = _d
                else:
                    dst_core_node = self.core_nodes[dst_name]
                addtl_conns = src_core_node.connect(dst_core_node, edge, kwargs)
            else:
                addtl_conns = self.core_nodes[src_name].connect(self.core_nodes[dst_name], edge)
            if addtl_conns is not None:
                self.nlb.add_connections(addtl_conns, defer_placement=True)

    def configure_cores(self):
        '''
        Go through nodes and configure each based on the attributes...
        '''
        for node in self.graph.get_nodes():
            node_attr = node.get_attributes()
            if self.use_fa and isinstance(self.core_nodes[node.get_name()], tuple):
                core, flavor = self.core_nodes[node.get_name()]
                node_config_ret = core.configure(node_attr, flavor)
            else:
                node_config_ret = self.core_nodes[node.get_name()].configure(node_attr)
            if node_config_ret is not None:
                node_config_tuple, node_config_kwargs = node_config_ret
            else:
                node_config_kwargs = {}
            # GLB tiles return none so that we don't try to config map them...
            if self.bespoke:
                if node_attr['hwnode'] == 'HWNodeType.GLB':
                    continue
                node_name = node.get_name()
                # node_inst = self.fabric[self.core_gens[node_name].get_name()]
                node_inst = self.core_gens[node_name]
                if node_attr['hwnode'] == 'HWNodeType.Memory':
                    node_cfg = node_inst.get_bitstream(node_config_kwargs)
                else:
                    node_cfg = node_inst.get_bitstream(**node_config_kwargs)
                # Now for the configurations, wire them directly
                for cfg_port, cfg_val in node_cfg:
                    # Now we need the flattened wrapper/actually used instance
                    child_inst = self.fabric[self.core_nodes[node.get_name()].get_name()]
                    self.fabric.wire(child_inst.ports[cfg_port], kratos.const(cfg_val, child_inst.ports[cfg_port].width))

            else:
                if node_attr['hwnode'] == 'HWNodeType.GLB':
                    if self.verbose:
                        print("SAW GLB...skipping")
                if isinstance(self.core_nodes[node.get_name()], tuple):
                    core_node, flavor = self.core_nodes[node.get_name()]
                else:
                    core_node = self.core_nodes[node.get_name()]
                if self.verbose:
                    print(f"Node name --- {core_node.get_name()}")
                # Hack for now - identify core combiner nodes and pass them the kwargs
                if "m" in core_node.get_name() or "p" in core_node.get_name():
                    runtime_modes = self.nlb.get_core_runtimes()
                    runtime_mode = runtime_modes[core_node.get_name()]
                    # Now need to set the runtime
                    node_config_kwargs['mode'] = runtime_mode
                    pass_config_kwargs_tuple = (1, node_config_kwargs)
                    self.nlb.configure_tile(core_node.get_name(), pass_config_kwargs_tuple)
                else:
                    if "glb" in node.get_name():
                        node_config_kwargs['ready_valid_mode'] = 1  # maybe to add?
                    self.nlb.configure_tile(core_node.get_name(), (1, node_config_kwargs))

    def display_names(self):
        if self.bespoke:
            for key, val in self.name_maps.items():
                print(f"{key} => {val}")
        else:
            self.nlb.display_names()

    def dump_display_names(self, output_file):
        with open(output_file, "w+") as outfile_handle:
            if self.bespoke:
                for key, val in self.name_maps.items():
                    outfile_handle.write(f"{key} => {val}")
            else:
                to_print = self.nlb.display_names(print_v=False)
                outfile_handle.writelines(to_print)

    def get_core_placement(self, core):
        return self.nlb.get_core_placement(core)

    def add_plus_arg(self, new_parg):
        self.plus_args.append(new_parg)

    def dump_plus_args(self, fp_, input_dir=None, output_dir=None, collat_dir=None):

        if input_dir is None:
            input_dir = self.input_dir

        if output_dir is None:
            output_dir = self.output_dir

        if collat_dir is None:
            collat_dir = self.collat_dir

        with open(fp_, 'w+') as fp_handle:
            for parg in self.plus_args:
                if isinstance(parg, tuple):
                    to_write_pholder = parg[0]
                    if parg[1] == 'input':
                        to_write_wo_pholder = to_write_pholder.format(input_dir)
                        # Also add in the tx_size here...
                        file_path_from_parg = to_write_wo_pholder[9:].split('=')[1]
                        file_path_from_parg_no_quotes = file_path_from_parg.strip().strip('\"')
                        len_file = 0
                        try:
                            with open(file_path_from_parg_no_quotes, 'r') as fd_temp_:
                                len_file = len(fd_temp_.readlines())
                        except:
                            len_file = 0
                        tx_size_line = f"{to_write_pholder[0:8]}_TX_SIZE={len_file}\n"
                        fp_handle.write(tx_size_line)
                    elif parg[1] == 'collat':
                        to_write_wo_pholder = to_write_pholder.format(collat_dir)
                    else:
                        to_write_wo_pholder = to_write_pholder.format(output_dir)
                    fp_handle.write(to_write_wo_pholder)
                else:
                    fp_handle.write(parg)


def prepare_glb_collateral(glb_dir=None, bitstream=None, matrices_in=None, design_place=None, glb_info=None, test_dump_dir=None, opal_workaround=False):

    assert glb_dir is not None
    assert bitstream is not None
    assert matrices_in is not None
    assert design_place is not None
    assert glb_info is not None

    if not os.path.exists(glb_dir):
        os.mkdir(glb_dir)

    shutil.copytree(test_dump_dir, f"{glb_dir}/bin", dirs_exist_ok=True, ignore=shutil.ignore_patterns('*.graph'))

    input_glb_tiles = [glb_tile for glb_tile in glb_info if glb_tile[3] == 'write']
    output_glb_tiles = [glb_tile for glb_tile in glb_info if glb_tile[3] == 'read']

    # Loop through the input matrices and create raw versions
    # for filename in os.listdir(matrices_in):
    for idx_, input_glb_tile in enumerate(input_glb_tiles):
        (core, core_placement, tensor_desc_str, direction, num_blocks, seg_mode, file_number_) = input_glb_tile
        assert os.path.exists(f"{matrices_in}/{tensor_desc_str}")
        os.system(f"xxd -r -p {matrices_in}/{tensor_desc_str} > {glb_dir}/bin/{tensor_desc_str}.raw")
        with open(f"{matrices_in}/{tensor_desc_str}") as tmp_fp:
            num_lines = len(tmp_fp.readlines())
        input_glb_tiles[idx_] = (core, core_placement, tensor_desc_str, num_lines, num_blocks, seg_mode, file_number_)

    design_meta_json = {}
    design_meta_json["testing"] = {
        "interleaved_input": [
            "input.pgm"
        ],
        "interleaved_output": [
            "gold.pgm"
        ],
        "bitstream": "bitstream.bs",
        "coreir": "design_top.json",
        "placement": "design.place",
    }
    if opal_workaround:
        design_meta_json["testing"]["opal_dense_scanner_workaround"] = 1
    design_meta_json["IOs"] = {
        "inputs": [],
        "outputs": [],
        "mu_inputs": []
    }

    tmp_json = None
    for input_glb_tile in input_glb_tiles:
        (core, core_placement, tensor_desc_str, num_lines, num_blocks, seg_mode, file_number) = input_glb_tile
        tmp_json = {
            "bitwidth": 16,
            "datafile": f"{tensor_desc_str}.raw",
            "name": f"{tensor_desc_str}",
            "shape": [num_lines],
            "io_tiles": [
                {
                    "name": f"{tensor_desc_str}",
                    "mode": "RV",
                    "addr": {
                        "cycle_starting_addr": [0],
                        "cycle_stride": [1],
                        "dimensionality": 1,
                        "extent": [num_lines],
                        "read_data_starting_addr": [0],
                        "read_data_stride": [1]
                    },
                    "x_pos": core_placement[0],
                    "y_pos": core_placement[1]
                }
            ]
        }
        design_meta_json["IOs"]["inputs"].append(tmp_json)

    for idx_, output_glb_tile in enumerate(output_glb_tiles):
        (core, core_placement, tensor_desc_str, direction, num_blocks, seg_mode, file_number) = output_glb_tile
        # print("tensor desc str: ", tensor_desc_str)
        # print("file number: ", file_number)
        # print("glb dir: ", glb_dir)
        assert os.path.exists(f"{glb_dir}/{tensor_desc_str}_{file_number}")

        os.system(f"xxd -r -p {glb_dir}/{tensor_desc_str}_{file_number} > {glb_dir}/bin/{tensor_desc_str}.raw")
        with open(f"{glb_dir}/{tensor_desc_str}_{file_number}") as tmp_fp:
            num_lines = len(tmp_fp.readlines())
        output_glb_tiles[idx_] = (core, core_placement, tensor_desc_str, num_lines, num_blocks, seg_mode, file_number)

    tmp_json = None
    for output_glb_tile in output_glb_tiles:
        (core, core_placement, tensor_desc_str, num_lines, num_blocks, seg_mode, file_number) = output_glb_tile
        tmp_json = {
            "bitwidth": 16,
            "datafile": f"{tensor_desc_str}.raw",
            "name": f"{tensor_desc_str}",
            "shape": [num_lines],
            "io_tiles": [
                {
                    "name": f"{tensor_desc_str}",
                    "mode": "RV",
                    "num_blocks": num_blocks,
                    "seg_mode": seg_mode,
                    "addr": {
                        "cycle_starting_addr": [0],
                        "cycle_stride": [1],
                        "dimensionality": 1,
                        # "extent": [num_lines],
                        # HAX for testing against GLB
                        "extent": [32768],
                        "write_data_starting_addr": [0],
                        "write_data_stride": [1]
                    },
                    "x_pos": core_placement[0],
                    "y_pos": core_placement[1]
                }
            ]
        }
        design_meta_json["IOs"]["outputs"].append(tmp_json)

    with open(f"{glb_dir}/bin/design_meta.json", "w+") as metafile:
        json.dump(design_meta_json, metafile)


def write_glb_file(file_list, out_dir, out_name, use_fp=False):
    output_lines = []
    # for seed flow
    if not give_tensor:
        output_lines.append(f"{0:04X}\n")

    for f in file_list:
        with open(f, 'r') as curr_file:
            all_lines = curr_file.readlines()
            # Get rid of 0x for readmemh compatibility
            # hexified = str(hex(len(all_lines)))[2:]
            output_lines.append(f"{len(all_lines):04X}\n")
            for l in all_lines:
                if not use_fp:
                    # convert to an integer
                    temp_tkn = int(float(l.strip()))
                    if temp_tkn >= (2 ** 16):
                        temp_tkn = temp_tkn - (((temp_tkn // (2 ** 16)) * (2 ** 16)))
                    output_lines.append(f"{hex(temp_tkn & 0xFFFF)[2:].zfill(4)}\n")
                else:
                    tmp_tkn = float(l.strip())
                    output_lines.append(f"{hex(int(float2bfbin(tmp_tkn), 2))[2:].zfill(4)}\n")
    out_path = f"{out_dir}/{out_name}"
    with open(out_path, "w+") as curr_file:
        curr_file.writelines(output_lines)


def coalesce_files(in_dir, out_dir, hack_files=None, unroll=1, give_tensor=None, use_fp=False):
    # Hack to inject handmade files directly
    if hack_files is not None:
        for hack_file in hack_files:
            tmp_lines = None
            with open(hack_file, "r") as hf_handle:
                tmp_lines = hf_handle.readlines()
            with open(f"{out_dir}/{hack_file}", "w+") as out_hf_handle:
                out_hf_handle.writelines(tmp_lines)
        return

    # First, find the unique guys in the in_dir (tensors)
    tensors = {}
    all_in_files = os.listdir(in_dir)
    for fname in all_in_files:
        if "vals" not in fname:
            continue
        tname = fname.replace("tensor_", "").replace("_mode_vals", "")
        if tname not in tensors:
            tensors[tname] = 1
    for tname, _ in tensors.items():
        # Assume everything CSF right now - always a seg/crd array
        # mode_num = 0
        # done = False
        for copy_ in range(unroll):
            mode_num = 0
            done = False
            while done is False:
                if f'tensor_{tname}_mode_{mode_num}_seg' in all_in_files and \
                        f'tensor_{tname}_mode_{mode_num}_crd' in all_in_files:
                    # Now coalesce the seg/crd into a single file
                    write_glb_file([f'{in_dir}/tensor_{tname}_mode_{mode_num}_seg',
                                   f'{in_dir}/tensor_{tname}_mode_{mode_num}_crd'],
                                   out_dir=out_dir, out_name=f'tensor_{tname}_mode_{mode_num}')
                    mode_num = mode_num + 1
                elif f'tensor_{tname}_mode_{mode_num}_seg' in all_in_files:
                    write_glb_file([f'{in_dir}/tensor_{tname}_mode_{mode_num}_seg'],
                                   out_dir=out_dir, out_name=f'tensor_{tname}_mode_{mode_num}')
                    mode_num = mode_num + 1
                else:
                    done = True
        # Now do vals
        for copy_ in range(unroll):
            if f'tensor_{tname}_mode_vals' in all_in_files:
                # TODO: This is a hack for now, get rid of this
                if tname not in ['fp_exp', 'fp_div']:
                    write_glb_file([f'{in_dir}/tensor_{tname}_mode_vals'],
                                   out_dir=out_dir, out_name=f'tensor_{tname}_mode_vals',
                                   use_fp=use_fp)
                else:
                    # the luts are dumped in bfloat16, transform it to hex for the sim by
                    # setting use_fp to True
                    write_glb_file([f'{in_dir}/tensor_{tname}_mode_vals'],
                                   out_dir=out_dir, out_name=f'tensor_{tname}_mode_vals',
                                   use_fp=True)


def lego_generate_inputs(app_name):
    # Use lego to generate input matrices
    input_file_dir = os.path.join("input/aha_regress", app_name)
    program_file = os.path.join(input_file_dir, "program.txt")
    tensor_file = os.path.join(input_file_dir, "tensor.txt")
    try:
        print(f"=== Lego Generating CPP Code ===")
        tile = subprocess.run(["python", "main.py",
                               "--program", program_file,
                               "--tensor", tensor_file,
                               "--output_dir", "/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR",
                               "--mode", "rtl"],
                              cwd="/aha/Lego_v0")
        tile.check_returncode()
    except subprocess.CalledProcessError as e:
        print(e.stderr)
        raise RuntimeError("Lego failed to generate input matrices")

    try:
        print(f"=== Lego Compiling CPP Code ===")
        tile = subprocess.run(["g++", "-o", "main", "main.cpp",
                               "src/data_parser.cpp",
                               "src/mem_op.cpp",
                               "src/activation.cpp",
                               "src/bf16_op.cpp",
                               "src/gen_lut.cpp"],
                              cwd="/aha/Lego_v0")
        tile.check_returncode()
    except subprocess.CalledProcessError as e:
        print(e.stderr)
        raise RuntimeError("Lego failed to generate input matrices")

    try:
        print(f"=== Lego Tiling ===")
        tile = subprocess.run(["./main", "tiling"], cwd="/aha/Lego_v0")
        tile.check_returncode()
    except subprocess.CalledProcessError as e:
        print(e.stderr)
        raise RuntimeError("Lego failed to generate input matrices")

    subtile_paths_list = os.path.join("/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR", app_name, "subtile_paths_0.toml")
    with open(subtile_paths_list, 'r') as f:
        tile_pairs_dict = toml.load(f)
        data_tile_pairs = tile_pairs_dict["sam_config"]["sam_path"]
        # FIXME: for now, only supports testing a single tile
        assert len(data_tile_pairs) == 1
    matrix_tmp_dir = os.path.join("/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR", app_name, data_tile_pairs[0])

    return matrix_tmp_dir


def hardcode_generate_intpus(app_name, matrix_tmp_dir, give_tensor=False, tensor_orderings=None, clean=True, suffix=""):
    # these application does not have an einsum expression, falling back to the old flow to
    os.makedirs(matrix_tmp_dir, exist_ok=True)
    use_fp = False

    if app_name == "trans_masked_broadcast":
        B_mat = get_tensor(input_name='B', shapes=[10, 10], give_tensor=give_tensor, tmp_dir=matrix_tmp_dir,
                           dump=matrix_tmp_dir, suffix=suffix, clean=clean, tensor_ordering=tensor_orderings['B'],
                           sparsity=0.5)
        c_mat = get_tensor(input_name='c', shapes=[10], give_tensor=give_tensor, tmp_dir=matrix_tmp_dir,
                           dump=matrix_tmp_dir, suffix=suffix, clean=False, tensor_ordering=tensor_orderings['c'],
                           sparsity=0.0)
        assert c_mat.shape[0] == B_mat.shape[0]

        output_matrix = numpy.zeros((10, 10), dtype=numpy.uint16)
        for i in range(0, output_matrix.shape[0]):
            for j in range(0, output_matrix.shape[1]):
                if B_mat[i][j] != 0:
                    output_matrix[i][j] = c_mat[i]
        output_format = "CSF"
        output_name = "X"
    elif app_name == "masked_broadcast":
        B_mat = get_tensor(input_name='B', shapes=[10, 10], give_tensor=give_tensor, tmp_dir=matrix_tmp_dir,
                           dump=matrix_tmp_dir, suffix=suffix, clean=clean, tensor_ordering=tensor_orderings['B'],
                           sparsity=0.5)
        c_mat = get_tensor(input_name='c', shapes=[10], give_tensor=give_tensor, tmp_dir=matrix_tmp_dir,
                           dump=matrix_tmp_dir, suffix=suffix, clean=False, tensor_ordering=tensor_orderings['c'],
                           sparsity=0.0)
        assert c_mat.shape[0] == B_mat.shape[0]

        output_matrix = numpy.zeros((10, 10), dtype=numpy.uint16)
        for i in range(0, output_matrix.shape[0]):
            for j in range(0, output_matrix.shape[1]):
                if B_mat[i][j] != 0:
                    output_matrix[i][j] = c_mat[j]
        output_format = "CSF"
        output_name = "X"
    elif app_name == "mat_mattransmul":  # remove this special case once lego is fixed
        vec_ordering = ((1, (0, 's')),)
        b_mat = get_tensor(input_name='b', shapes=[1], give_tensor=give_tensor, tmp_dir=matrix_tmp_dir,
                           dump=matrix_tmp_dir, suffix=suffix, clean=clean, tensor_ordering=tensor_orderings['b'],
                           sparsity=0)
        C_mat = get_tensor(input_name='C', shapes=[10, 10], give_tensor=give_tensor, tmp_dir=matrix_tmp_dir,
                           dump=matrix_tmp_dir, suffix=suffix, clean=False, tensor_ordering=tensor_orderings['C'],
                           sparsity=0.8)
        d_mat = get_tensor(input_name='d', shapes=[10], give_tensor=give_tensor, tmp_dir=matrix_tmp_dir,
                           dump=matrix_tmp_dir, suffix=suffix, clean=False, tensor_ordering=tensor_orderings['d'],
                           sparsity=0.9)
        e_mat = get_tensor(input_name='e', shapes=[1], give_tensor=give_tensor, tmp_dir=matrix_tmp_dir,
                           dump=matrix_tmp_dir, suffix=suffix, clean=False, tensor_ordering=tensor_orderings['e'],
                           sparsity=0)
        f_mat = get_tensor(input_name='f', shapes=[10], give_tensor=give_tensor, tmp_dir=matrix_tmp_dir,
                           dump=matrix_tmp_dir, suffix=suffix, clean=False, tensor_ordering=tensor_orderings['f'],
                           sparsity=0.8)

        output_matrix = numpy.add(numpy.multiply(e_mat, f_mat, dtype=numpy.uint16, casting='unsafe'),
                                  numpy.multiply(b_mat,
                                                 numpy.matmul(C_mat, d_mat,
                                                              dtype=numpy.uint16,
                                                              casting='unsafe'),
                                                 dtype=numpy.uint16,
                                                 casting='unsafe'),
                                  dtype=numpy.uint16, casting='unsafe')
        output_format = "CSF"
        output_name = "x"

    return output_matrix, output_format, output_name, use_fp


def read_lego_gold(matrix_tmp_dir, tensor_orderings):
    # Read the gold matrix
    output_dims = []
    use_fp = False
    with open(f"{matrix_tmp_dir}/tensor_out_mode_shape", "r") as f:
        lines = f.readlines()
        for line in lines:
            output_dims.append(int(line.strip()))

    output_format = "CSF"
    output_name = None
    # vector outputs have the name 'x'
    # tensors of 2 or higher dimensions have the name 'X'
    if len(output_dims) == 1:
        output_name = "x"
    else:
        output_name = "X"

    output_matrix = numpy.zeros(output_dims, dtype=numpy.float32)

    # Transpose since the gold matrix may be filled in column order if the
    # tensor ordering is 10
    rearrng_axis = []
    output_mode_map = tensor_orderings[output_name]
    for reorder_tup in output_mode_map:
        rearrng_axis.append(reorder_tup[0])

    is_scalar = (rearrng_axis == [])
    if not is_scalar:
        output_matrix = numpy.transpose(output_matrix, rearrng_axis)
    with open(f"{matrix_tmp_dir}/output_gold.h", "r") as f:
        for idx, _ in numpy.ndenumerate(output_matrix):
            output_matrix[idx] = float(f.readline().strip())
    # transpose it back to the original shape
    if not is_scalar:
        output_matrix = numpy.transpose(output_matrix, rearrng_axis)

    # parse the data type of the input and the output
    with open(f"{matrix_tmp_dir}/dtype", "r") as f:
        dtype = f.readline().strip()
    if dtype == "bf16":
        use_fp = True

    return output_matrix, output_format, output_name, use_fp


def generate_inputs_and_gold(app_name, give_tensor=False, print_inputs=None,
                             tensor_orderings=None, clean=True, suffix=""):

    MAXIMUM_SIZES = 16

    assert tensor_orderings is not None

    output_matrix = None
    output_format = None

    input_tensors = dict()

    b_mat = None
    c_mat = None
    d_mat = None

    output_name = None
    input_dims = {}
    use_fp = False

    lego_unsupported_apps = ["masked_broadcast", "trans_masked_broadcast", "mat_mattransmul"]

    # generate inputs and read gold matrix
    if app_name in lego_unsupported_apps:
        if give_tensor:
            matrix_tmp_dir = os.path.join(tensor_locs, kernel_name, seed)
        else:
            matrix_tmp_dir = os.path.join("/aha/garnet/SPARSE_TESTS/MAT_TMP_DIR", app_name, "tile_0")
        output_matrix, output_format, output_name, use_fp = hardcode_generate_intpus(app_name,
                                                                                     matrix_tmp_dir,
                                                                                     give_tensor=give_tensor,
                                                                                     tensor_orderings=tensor_orderings,
                                                                                     clean=clean, suffix=suffix)
    else:
        if give_tensor:
            matrix_tmp_dir = os.path.join(tensor_locs, kernel_name, seed)
        else:
            matrix_tmp_dir = lego_generate_inputs(app_name)
        output_matrix, output_format, output_name, use_fp = read_lego_gold(matrix_tmp_dir, tensor_orderings)
    if print_inputs is not None:
        if b_mat is not None:
            input_tensors["B"] = b_mat
        if c_mat is not None:
            input_tensors["C"] = c_mat
        if d_mat is not None:
            input_tensors["D"] = d_mat

        original_stdout = sys.stdout
        with open(print_inputs, 'w+') as inf:
            sys.stdout = inf
            for name, vals in input_tensors.items():
                print(f"{name}")
                print(vals)
            sys.stdout = original_stdout

    return output_matrix, output_format, output_name, input_dims, use_fp, matrix_tmp_dir


def create_or_clean(dir_path):
    if not os.path.isdir(dir_path):
        # os.mkdir(dir_path)
        os.makedirs(dir_path)
    else:
        # Otherwise clean it
        for filename in os.listdir(dir_path):
            full_del_path = dir_path + "/" + filename
            if os.path.isfile(full_del_path):
                ret = os.remove(full_del_path)
            elif os.path.isdir(full_del_path):
                ret = shutil.rmtree(full_del_path)


def prep_test_dir(base_dir, dir_arg, sub_dir):
    if dir_arg is None:
        ret_dir = f"{base_dir}/{sub_dir}"
    else:
        ret_dir = dir_arg
    create_or_clean(ret_dir)
    ret_dir = os.path.abspath(ret_dir)
    return ret_dir


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Sparse TB Generator')
    # parser.add_argument('--sam_graph', type=str, default=None)
    parser.add_argument('--sam_graph', type=str, default=None, nargs='+')
    parser.add_argument('--output_dir', type=str, default=None)
    parser.add_argument('--input_dir', type=str, default=None)
    parser.add_argument('--test_dump_dir', type=str, default=None)
    parser.add_argument('--matrix_tmp_dir', type=str, default=None)
    parser.add_argument('--gold_dir', type=str, default=None)
    parser.add_argument('--print_inputs', type=str, default=None)
    parser.add_argument('--fifo_depth', type=int, default=2)
    # parser.add_argument('--seed', type=int, default=0)
    parser.add_argument('--seed', type=int, default=0, nargs='+')
    parser.add_argument('--height', type=int, default=16)
    parser.add_argument('--width', type=int, default=32)
    parser.add_argument('--trace', action="store_true")
    parser.add_argument('--bespoke', action="store_true")
    parser.add_argument('--remote_mems', action="store_true")
    parser.add_argument('--ic_fork', action="store_true")
    parser.add_argument('--give_tensor', action="store_true")
    # parser.add_argument('--tensor_locs', type=str, default=None, nargs='+')
    parser.add_argument('--tensor_locs', type=str, default=None)
    parser.add_argument('--physical_sram', action="store_true")
    parser.add_argument('--just_verilog', action="store_true")
    parser.add_argument('--clk_enable', action="store_true")
    parser.add_argument('--gen_pe', action="store_true")
    parser.add_argument('--add_pond', action="store_true")
    parser.add_argument('--combined', action="store_true")
    parser.add_argument('--pipeline_scanner', action="store_true")
    parser.add_argument('--dump_bitstream', action="store_true")
    parser.add_argument('--no_harden_flush', action="store_true")
    parser.add_argument('--dump_glb', action="store_true")
    parser.add_argument('--verbose', action="store_true")
    parser.add_argument('--glb_dir', type=str, default=None)
    parser.add_argument('--just_glb', action="store_true")
    parser.add_argument('--fiber_access', action="store_true")
    parser.add_argument('--base_dir', type=str, default=None)
    parser.add_argument('--fault', action="store_true")
    parser.add_argument('--gen_verilog', action="store_true")
    parser.add_argument('--zero_input', action="store_true")
    parser.add_argument('--do_comparison', action="store_true")
    parser.add_argument('--run', type=str, default=None)
    parser.add_argument('--gold_mat_dir', type=str, default=None)
    parser.add_argument('--sim_mat_dir', type=str, default=None)
    parser.add_argument('--sim_dir', type=str, default='/aha/garnet/SIM_DIR')
    parser.add_argument('--mem_width', type=int, default=64)
    parser.add_argument('--compile_tb', action="store_true")
    parser.add_argument('--perf_debug', action="store_true")
    parser.add_argument('--unroll', type=int, default=1)
    parser.add_argument('--data_tile_pairs', type=str, default=None, nargs='+')
    parser.add_argument('--kernel_name', type=str, default=None)
    parser.add_argument('--opal-workaround', action="store_true")
    parser.add_argument('--mem_block_size', type=int, default=2048)
    parser.add_argument('--using-matrix-unit', action="store_true")
    parser.add_argument('--give-north-io-sbs', action="store_true")
    parser.add_argument("--num-fabric-cols-removed", default=0, type=int)
    parser.add_argument('--include-E64-hw', action="store_true")
    parser.add_argument('--use-non-split-fifos', action="store_true")

    args = parser.parse_args()
    bespoke = args.bespoke
    use_fork = args.ic_fork
    seeds = args.seed
    give_tensor = args.give_tensor
    fifo_depth = args.fifo_depth
    physical_sram = args.physical_sram
    just_verilog = args.just_verilog
    clk_enable = args.clk_enable
    gen_pe = args.gen_pe
    add_pond = args.add_pond
    combined = args.combined
    sam_graphs = args.sam_graph
    pipeline_scanner = args.pipeline_scanner
    dump_bitstream = args.dump_bitstream
    harden_flush = not args.no_harden_flush
    print_inputs = args.print_inputs
    dump_glb = args.dump_glb
    chip_h = args.height
    chip_w = args.width
    just_glb = args.just_glb
    use_fiber_access = args.fiber_access
    verbose = args.verbose
    fault = args.fault
    gen_verilog = args.gen_verilog
    zero_input = args.zero_input
    do_comparison = args.do_comparison
    gold_mat_dir = args.gold_mat_dir
    sim_mat_dir = args.sim_mat_dir
    sim_dir = args.sim_dir
    mem_width = args.mem_width
    mtx_tmp_dir = args.matrix_tmp_dir
    tensor_locs = args.tensor_locs
    run_all = args.run
    compile_tb = args.compile_tb
    perf_debug = args.perf_debug
    unroll = args.unroll
    data_tile_pairs = args.data_tile_pairs
    kernel_name = args.kernel_name
    opal_workaround = args.opal_workaround
    mem_block_size = args.mem_block_size
    using_matrix_unit = args.using_matrix_unit
    give_north_io_sbs = args.give_north_io_sbs
    num_fabric_cols_removed = args.num_fabric_cols_removed
    include_E64_hw = args.include_E64_hw
    use_non_split_fifos = args.use_non_split_fifos

    if include_E64_hw:
        os.environ["INCLUDE_E64_HW"] = "1"

    if use_non_split_fifos:
        os.environ["USE_NON_SPLIT_FIFOS"] = "1"

    if using_matrix_unit:
        if num_fabric_cols_removed == 0:
            io_sides = [IOSide.North, IOSide.West]
        else:
            io_sides = [IOSide.North]
    else:
        io_sides = [IOSide.North]

    # Unreachable for ss regress flow
    if do_comparison:
        # This is where we do the fallback comparison...
        # First get gold matrix from the output...
        for i in range(unroll):
            gold_matrix = numpy.load(f"{gold_mat_dir}/output_gold_{i}.npy", allow_pickle=True)
            name_line = None
            with open(f"{gold_mat_dir}/output_name.txt") as output_name_h_:
                name_line = output_name_h_.readlines()[0].strip()
            output_name = name_line
            assert output_name is not None

            sim_matrix = get_tensor_from_files(name='X', files_dir=sim_mat_dir,
                                               format="CSF",
                                               shape=gold_matrix.shape, base=16, early_terminate='x', suffix=f"_{i}")
            sim_matrix_np = sim_matrix.get_matrix()

            print(f"GOLD_{i}")
            gold_matrix = gold_matrix.astype(numpy.uint16, casting='unsafe')
            print(gold_matrix)
            print(f"SIM_{i}")
            sim_matrix_np = sim_matrix_np.astype(numpy.uint16, casting='unsafe')
            print(sim_matrix)

            assert numpy.array_equal(gold_matrix, sim_matrix_np)

        exit()

    print(sam_graphs)

    test_mem_core_dir = os.path.dirname(__file__)

    if not os.path.isdir(sim_dir):
        os.mkdir(sim_dir)
    test_dump_dir = sim_dir

    # Unreachable for ss regress flow
    if run_all is not None:

        for test_module in glob.glob(os.path.join(test_mem_core_dir, "*.*v")):
            shutil.copy(test_module, test_dump_dir)
        shutil.copy(os.path.join(test_mem_core_dir, "Makefile"), test_dump_dir)
        shutil.copy(os.path.join(test_mem_core_dir, "run_sim.tcl"), test_dump_dir)
        # cw_dir = "/cad/cadence/GENUS_19.10.000_lnx86/share/synth/lib/chipware/sim/verilog/CW/"
        cw_dir = "/cad/cadence/GENUS_19.10.000_lnx86/share/synth/lib/chipware/sim/verilog/CW/"
        shutil.copy(os.path.join(test_mem_core_dir, "../../peak_core/CW_fp_add.v"), test_dump_dir)
        shutil.copy(os.path.join(test_mem_core_dir, "../../peak_core/CW_fp_mult.v"), test_dump_dir)
        gemstone_dir = os.path.dirname(os.path.dirname(gemstone.__file__))
        for aoi_mux in glob.glob(os.path.join(gemstone_dir, "tests", "common", "rtl", "*.sv")):
            shutil.copy(aoi_mux, test_dump_dir)

        my_env = os.environ
        my_env['WAVEFORM'] = "0"
        if args.trace:
            my_env['WAVEFORM'] = "1"
        # my_env['TEST_ARGS'] = f"{collat_dir}/PARGS.txt"

        base_dir = args.base_dir
        bd = f"{os.path.abspath(base_dir)}"
        if run_all == "all":
            tests_to_run = os.listdir(bd)
        else:
            tests_to_run = [f'{run_all}']

        local_comp = True

        for test_ in tests_to_run:

            my_env['TEST_DIR'] = f"{os.path.abspath(base_dir)}/{test_}"
            my_env['UNROLL'] = f"{unroll}"

            if local_comp and compile_tb:
                t_c = time.time()
                subprocess.check_call(
                    ["make", "compile"],
                    cwd=test_dump_dir,
                    env=my_env
                )

            local_comp = False

            try:

                t_r = time.time()
                subprocess.check_call(
                    ["make", "run"],
                    cwd=test_dump_dir,
                    env=my_env
                )

            except Exception:
                print("Failed for some reason...")

        print("Finished running!...Quitting...")
        exit()

    pnr_only = (just_glb or not fault) and not gen_verilog

    assert len(sam_graphs) > 0, f"No sam graph pointed to..."

    # Make sure to force DISABLE_GP for much quicker runs
    os.environ['DISABLE_GP'] = '1'

    pe_prefix = "PEGEN_"
    real_pe = True

    # Create PE verilog for inclusion...
    if gen_pe is True:
        pe_child = PE_fc(family.MagmaFamily())
        m.compile(f"{test_mem_core_dir}/PE", pe_child, output="coreir-verilog", coreir_libs={"float_CW"}, verilog_prefix=pe_prefix)
        m.clear_cachedFunctions()
        m.frontend.coreir_.ResetCoreIR()
        m.generator.reset_generator_cache()
        m.logging.flush_all()  # flush all staged logs

    nlb = None
    interconnect = None
    if bespoke is False:
        chip_width = chip_w
        chip_height = chip_h
        num_tracks = 5

        time_0 = time.time()

        interconnect = create_cgra(input_width=chip_width, input_height=chip_height,
                                   io_sides=io_sides,
                                   using_matrix_unit=using_matrix_unit,
                                   num_tracks=num_tracks,
                                   add_pd=False,
                                   # Soften the flush...?
                                   harden_flush=harden_flush,
                                   altcore=None,
                                   add_pond=add_pond,
                                   scgra=True,
                                   perf_debug=perf_debug,
                                   give_north_io_sbs=give_north_io_sbs,
                                   num_fabric_cols_removed=num_fabric_cols_removed,
                                   include_E64_hw=include_E64_hw)

        time_x = time.time()
        # print(f"TIME:\tcreate_cgra\t{time_x - time_0}")

        if just_verilog:
            circuit = interconnect.circuit()
            import magma
            magma.compile(f"{test_dump_dir}/SparseTBBuilder", circuit, coreir_libs={"float_CW"})
            exit()

        west_in_io_sides = IOSide.West in io_sides
        nlb = NetlistBuilder(interconnect=interconnect, cwd=test_dump_dir,
                             harden_flush=harden_flush, combined=combined,
                             pnr_only=pnr_only, west_in_io_sides=west_in_io_sides)

        time_1 = time.time()
        # print(f"TIME:\tnlb\t{time_1 - time_x}")

    stb_to_gen = None

    with tempfile.TemporaryDirectory() as base_dir_td:

        if args.base_dir is None:
            base_dir = base_dir_td.name
        else:
            base_dir = args.base_dir
            if not os.path.isdir(base_dir):
                os.mkdir(base_dir)

        print(f"BASE DIR BEING USED:\t{base_dir}")

        for sam_graph in sam_graphs:

            # sam_graph = sam_graph.replace("onyx-dot", "dot")
            print(f"SAM GRAPH:\t{sam_graph}")

            sdgs = {}
            mode_maps = []
            graphs = []
            stbs = {}

            output_dirs = []
            input_dirs = []
            matrix_tmp_dirs = []
            gold_dirs = []
            glb_dirs = []
            collat_dirs = []

            sam_graph_name = sam_graph.split('/')[-1].split(".")[0]

            if isinstance(seeds, int):
                seeds = [seeds]
            use_seeds = seeds

            if give_tensor:
                use_seeds = data_tile_pairs

            for seed in use_seeds:

                output_matrices = []
                output_formats = []
                output_names = []
                out_mats = []
                use_fp = False
                seed_id = None
                if not give_tensor:
                    numpy.random.seed(seed)
                    random.seed(seed)
                    seed_id = seed
                else:
                    # the "seed" here is the path to the input tile pair, we need to convert the path like string
                    # to a unique id for every tile pair
                    seed_id = kernel_name + "-" + seed.replace("/", "_")

                output_dir = prep_test_dir(f"{base_dir}/{sam_graph_name}_{seed_id}", args.output_dir, "OUTPUT_DIR")
                input_dir = prep_test_dir(f"{base_dir}/{sam_graph_name}_{seed_id}", args.input_dir, "INPUT_DIR")

                gold_dir = prep_test_dir(f"{base_dir}/{sam_graph_name}_{seed_id}", args.gold_dir, "GOLD_DIR")
                glb_dir = prep_test_dir(f"{base_dir}/{sam_graph_name}_{seed_id}", args.glb_dir, "GLB_DIR")
                collat_dir = prep_test_dir(f"{base_dir}/{sam_graph_name}_{seed_id}", args.glb_dir, "COLLAT_DIR")
                output_dirs.append(output_dir)
                input_dirs.append(input_dir)
                gold_dirs.append(gold_dir)
                glb_dirs.append(glb_dir)
                collat_dirs.append(collat_dir)

                if sam_graph not in sdgs:
                    print("SAM Graph Transformation")
                    sdg = SAMDotGraph(filename=sam_graph, local_mems=True, use_fork=use_fork,
                                      use_fa=use_fiber_access, unroll=unroll, collat_dir=collat_dir,
                                      opal_workaround=opal_workaround, mem_block_size=mem_block_size)
                    graph = sdg.get_graph()

                    # Add passthrough nodes out of refs and and in front of crddrop outers for better buffering
                    edges = graph.get_edges()
                    edges_to_edit = []
                    for edge in edges:
                        src = edge.get_source()
                        dst = edge.get_destination()
                        src_node = graph.get_node(src)
                        dst_node = graph.get_node(dst)
                        src_node_type = src_node[0].get_attributes()["type"]
                        dst_node_type = dst_node[0].get_attributes()["type"]
                        if "type" in edge.get_attributes():
                            edge_type = edge.get_attributes()["type"]
                        else:
                            edge_type = None
                        if "comment" in edge.get_attributes():
                            comment_type = edge.get_attributes()["comment"]
                        else:
                            comment_type = None
                        if src_node_type == '"fiberlookup"' and edge_type == '"ref"':
                            edges_to_edit.append(edge)
                        if dst_node_type == '"crddrop"' and 'outer' in comment_type.strip('"'):
                            edges_to_edit.append(edge)

                    # graph.write_png("/aha/before.png")
                    # Add node to edges
                    for edge in edges_to_edit:
                        src = edge.get_source()
                        dst = edge.get_destination()
                        src_node = graph.get_node(src)
                        dst_node = graph.get_node(dst)
                        attrs = copy.deepcopy(src_node[0].get_attributes())
                        og_label = attrs['label']
                        og_label = og_label.split('_')[0]
                        del attrs['label']
                        del attrs['hwnode']
                        if 'fa_color' in attrs:
                            del attrs['fa_color']
                        edge_attrs = copy.deepcopy(edge.get_attributes())
                        del edge_attrs['label']
                        edge_type = edge_attrs['type'].strip('"')

                        node_exists = graph.get_node(f"passthrough_buffer_{src}_{edge_type}")
                        if node_exists == []:
                            node = pydot.Node(f"passthrough_buffer_{src}_{edge_type}", **attrs, label=f"{og_label}_buffer_passthrough_{edge_type}", hwnode=f"{HWNodeType.PassThrough}")
                            graph.add_node(node)
                        else:
                            node = node_exists[0]

                        possible_edges = graph.get_edge(src, dst)
                        index = 0
                        for edge_check in possible_edges:
                            if edge.get_attributes() == edge_check.get_attributes():
                                break
                            index += 1
                        check = graph.del_edge(src, dst, index)

                        edge_to_passthrough_exists = graph.get_edge(src, node.get_name())
                        if edge_to_passthrough_exists == []:
                            edge1 = pydot.Edge(src=src_node[0], dst=node, **edge_attrs, label=f"pass_through_buffer0_{src}_{edge_type}",)
                            graph.add_edge(edge1)
                        edge2 = pydot.Edge(src=node, dst=dst_node[0], **edge_attrs, label=f"pass_through_buffer1_{src}_{edge_type}")
                        graph.add_edge(edge2)
                    # graph.write_png("/aha/after.png")
                    sdgs[sam_graph] = sdg
                else:
                    print("REUSE SDG")
                    sdg = sdgs[sam_graph]

                mode_map = sdg.get_mode_map()
                print(f"MODE MAP: {mode_map}")
                graph = sdg.get_graph()

                mode_maps.append(mode_map)
                graphs.append(graph)

                time_3 = time.time()

                # Need to unroll this as well
                clean = True
                # Assume we are unrolling 'B' for now... Update, change it to const 1
                for i in range(1):
                    ##### Handling app level file stuff #####
                    output_matrix, output_format, output_name, input_dims, use_fp, matrix_tmp_dir = generate_inputs_and_gold(sam_graph_name,
                                                                                                                             give_tensor,
                                                                                                                             print_inputs,
                                                                                                                             tensor_orderings=mode_map,
                                                                                                                             clean=clean,
                                                                                                                             suffix=f"")
                    if clean:
                        clean = False

                    output_matrices.append(output_matrix)
                    output_formats.append(output_format)
                    output_names.append(output_name)

                clean = True

                for i in range(1):  # change unroll to const 1
                    out_mat = MatrixGenerator(name=output_names[i], shape=None, sparsity=0.5,
                                              format=output_formats[i], dump_dir=gold_dir,
                                              tensor=output_matrices[i], clean=clean, use_fp=use_fp)

                    if clean:
                        clean = False

                    out_mat.dump_outputs()

                    out_mats.append(out_mat)

                if sam_graph not in stbs:
                    ##### Create the actual testbench mapping based on the SAM graph #####
                    # breakpoint()
                    print("Perform PnR")
                    stb = SparseTBBuilder(nlb=nlb, graph=graph, bespoke=bespoke, input_dir=input_dir,
                                          # output_dir=output_dir, local_mems=not args.remote_mems, mode_map=tuple(mode_map.items()))
                                          output_dir=output_dir, local_mems=True, mode_map=tuple(mode_map.items()),
                                          real_pe=real_pe, harden_flush=harden_flush, combined=combined,
                                          input_sizes=tuple(input_dims.items()), use_fa=use_fiber_access,
                                          verbose=verbose, pnr_only=pnr_only,
                                          width=chip_w, height=chip_h,
                                          collat_dir=collat_dir, give_tensor=give_tensor, west_in_io_sides=west_in_io_sides)
                    stbs[sam_graph] = stb
                    add_bs_args = True
                else:
                    stb = stbs[sam_graph]
                    add_bs_args = False

                if stb_to_gen is None:
                    stb_to_gen = stb
                    pnr_only = True

                if dump_glb:

                    # Want to dump specific tests...
                    test_name_base = sam_graph.split('/')[-1].split(".")[0]
                    print(f"TESTNAME: {test_name_base}")

                    if combined:
                        combined_str = "combined"
                    else:
                        combined_str = ""

                    full_test_name = f"{test_name_base}_{combined_str}_seed_{seed_id}"

                    full_test_glb_dir = f"{glb_dir}/{full_test_name}"

                    print(f"DUMPING TESTBENCH DATA TO: {full_test_glb_dir}")

                    # Make sure glb path exists
                    if not os.path.isdir(full_test_glb_dir):
                        os.mkdir(full_test_glb_dir)

                    for i in range(1):  # change unroll to const 1
                        out_mats[i].dump_outputs(glb_override=True, glb_dump_dir=full_test_glb_dir, suffix=f"_{i}")
                        numpy.save(f"{full_test_glb_dir}/output_gold_{i}.npy", out_mats[i].get_matrix())
                        numpy.save(f"{glb_dir}/output_gold_{i}.npy", out_mats[i].get_matrix())

                    with open(f"{glb_dir}/output_mode_map.json", "w+") as mode_map_file:
                        mode_map_file.write(json.dumps(mode_map[output_name]))
                    with open(f"{full_test_glb_dir}/output_mode_map.json", "w+") as mode_map_file:
                        mode_map_file.write(json.dumps(mode_map[output_name]))

                    with open(f"{glb_dir}/output_name.txt", "w+") as outputname_h_:
                        outputname_h_.write(f"{output_name}\n")
                    with open(f"{full_test_glb_dir}/output_name.txt", "w+") as outputname_h_:
                        outputname_h_.write(f"{output_name}\n")

                # Now coalesce them into combo files and put in final landing zone
                # First clear the out dir
                if not os.path.isdir(input_dir):
                    os.mkdir(input_dir)
                else:
                    # Otherwise clean it
                    for filename in os.listdir(input_dir):
                        ret = os.remove(input_dir + "/" + filename)

                # hack_in_files = ['./tensor_b_mode_0', './tensor_b_mode_vals']
                hack_in_files = None
                coalesce_files(in_dir=matrix_tmp_dir, out_dir=input_dir,
                               hack_files=hack_in_files, unroll=unroll,
                               give_tensor=give_tensor, use_fp=use_fp)

                # Clean up output dir...
                # If it doesn't exist, make it
                if not os.path.isdir(output_dir):
                    os.mkdir(output_dir)
                else:
                    # Otherwise clean it
                    for filename in os.listdir(output_dir):
                        ret = os.remove(output_dir + "/" + filename)

                time_2 = time.time()
                # print(f"TIME:\tglb\t{time_2 - time_1}")

                time_4 = time.time()
                # print(f"TIME:\tSTB\t{time_4 - time_3}")

                # collat_dir = collat_dirs[idx_]

                bs_size = nlb.write_out_bitstream(f"{collat_dir}/bitstream_nosp.bs", nospace=True, glb=False)
                if add_bs_args:
                    # stb.add_plus_arg(f"+BITSTREAM_LOCATION={collat_dir}/bitstream_nosp.bs")
                    stb.add_plus_arg((f"+BITSTREAM_LOCATION={{}}/bitstream_nosp.bs\n", 'collat'))
                    stb.add_plus_arg(f"+BITSTREAM_SIZE={bs_size}\n")
                # stb.dump_plus_args(f"{collat_dir}/PARGS.txt")
                stb.dump_plus_args(f"{collat_dir}/PARGS.txt", input_dir=input_dir, output_dir=output_dir, collat_dir=collat_dir)

                if dump_bitstream:
                    nlb.write_out_bitstream(f"{test_dump_dir}/bitstream.bs", nospace=False, glb=True)

                if dump_glb:
                    # breakpoint()
                    glb_info_ = []
                    glb_map = stb.get_glb_mapping()
                    mode_map = stb.get_mode_map()
                    for core, desc_ in glb_map.items():
                        tensor_, mode_, direction_, num_blocks_, seg_mode_, file_no_ = desc_
                        # remap the mode...
                        if mode_ != 'vals':
                            mode_ = mode_
                        core_placement = stb.get_core_placement(core)
                        tensor_desc_str = f"tensor_{tensor_}_mode_{mode_}"
                        glb_info_.append((core, core_placement, tensor_desc_str, direction_, num_blocks_, seg_mode_, file_no_))

                    # prepare_glb_collateral(glb_dir=glb_dir,
                    prepare_glb_collateral(glb_dir=full_test_glb_dir,
                                           bitstream=f"{test_dump_dir}/bitstream.bs",
                                           matrices_in=input_dir,
                                           design_place=f"{test_dump_dir}/design.place",
                                           glb_info=glb_info_,
                                           test_dump_dir=test_dump_dir,
                                           opal_workaround=opal_workaround)

                stb.display_names()
                stb.dump_display_names(f"{test_dump_dir}/design.mapped")
                stb.dump_display_names(f"{collat_dir}/design.mapped")

            nlb.reset()

            del stbs[sam_graph]

        # Need this before just_glb for early exits, not reachable for ss regress flow
        if not fault and gen_verilog:
            # Run the normal tb
            if gen_verilog:
                import magma
                magma.compile(f"{test_mem_core_dir}/SparseTBBuilder", stb_to_gen, coreir_libs={"float_CW"})
                print("MADE SPARSE TB: ")
                print(test_mem_core_dir)
                exit()

        if just_glb:  # ss regress flow ends here
            print("Only generating glb collateral and leaving...")
            exit()

        time_before_sim = time.time()

        if not fault:

            # Copy collateral...
            for test_module in glob.glob(os.path.join(test_mem_core_dir, "*.*v")):
                shutil.copy(test_module, test_dump_dir)
            shutil.copy(os.path.join(test_mem_core_dir, "Makefile"), test_dump_dir)
            shutil.copy(os.path.join(test_mem_core_dir, "run_sim.tcl"), test_dump_dir)
            # cw_dir = "/cad/cadence/GENUS_19.10.000_lnx86/share/synth/lib/chipware/sim/verilog/CW/"
            cw_dir = "/cad/cadence/GENUS_19.10.000_lnx86/share/synth/lib/chipware/sim/verilog/CW/"
            shutil.copy(os.path.join(test_mem_core_dir, "../../peak_core/CW_fp_add.v"), test_dump_dir)
            shutil.copy(os.path.join(test_mem_core_dir, "../../peak_core/CW_fp_mult.v"), test_dump_dir)
            gemstone_dir = os.path.dirname(os.path.dirname(gemstone.__file__))
            for aoi_mux in glob.glob(os.path.join(gemstone_dir, "tests", "common", "rtl", "*.sv")):
                shutil.copy(aoi_mux, test_dump_dir)

            my_env = os.environ
            my_env['WAVEFORM'] = "0"
            if args.trace:
                my_env['WAVEFORM'] = "1"

            my_env['TEST_DIR'] = f"{os.path.abspath(base_dir)}/{sam_graph_name}_{seed_id}"

            my_env['UNROLL'] = f"{unroll}"

            t_c = time.time()
            subprocess.check_call(
                ["make", "compile"],
                cwd=test_dump_dir,
                env=my_env
            )

            t_r = time.time()
            subprocess.check_call(
                ["make", "run"],
                cwd=test_dump_dir,
                env=my_env
            )

        else:
            ##### Create the actual testbench #####
            tester = BasicTester(stb, stb.clk, stb.rst_n)

            tester.zero_inputs()
            tester.poke(stb.io.stall, 1)
            tester.poke(stb.io.rst_n, 0)
            tester.eval()

            tester.step(2)
            tester.poke(stb.rst_n, 1)

            tester.step(2)
            # Stall during config
            tester.poke(stb.io.stall, 1)

            # After stalling, we can configure the circuit
            # with its configuration bitstream
            if nlb is not None:
                cfgdat = nlb.get_config_data()
                for addr, index in cfgdat:
                    tester.configure(addr, index)
                    # if readback is True:
                    #     self._tester.config_read(addr)
                    tester.eval()

                tester.done_config()

                tester.poke(stb.io.flush, 1)
                tester.eval()
                tester.step(2)
                tester.step(2)
                tester.step(2)
                tester.step(2)
                tester.step(2)
                tester.step(2)
                tester.step(2)
                tester.step(2)

                tester.poke(stb.io.stall, 0)
            tester.eval()

            # Get flush handle and apply flush to start off app
            tester.step(2)
            tester.step(2)

            tester.poke(stb.io.flush, 0)
            tester.eval()
            for i in range(50000):
                tester.step(2)
                tester_if = tester._if(tester.circuit.done)
                tester_if.print("Test is done...\n")
                tester_if.print("Cycle Count...%d\n", stb.io.cycle_count)
                tester_if.finish()

            from conftest import run_tb_fn
            run_tb_fn(tester, trace=args.trace, disable_ndarray=False, cwd=test_dump_dir, include_PE=True)

        time_after_sim = time.time()
        stb.display_names()

        ##### Now check it... #####
        for i in range(unroll):
            print(f"GOLD_{i}")
            print(output_matrices[i])

            sim_mat = get_tensor_from_files(name='X', files_dir=output_dir,
                                            format=output_format, shape=output_matrices[i].shape, base=16, early_terminate='x',
                                            suffix=f"_{i}")
            sim_mat_np = sim_mat.get_matrix()
            print(f"SIM_{i}")
            print(sim_mat_np)

            try:
                assert numpy.array_equal(output_matrices[i], sim_mat_np)
            except AssertionError as e:
                print(f"Test failed...output matrices are unequal")
                print(numpy.subtract(output_matrix, sim_mat_np))

        if fault:
            print(f"SIMULATION TIME:\t{time_after_sim - time_before_sim}")
        else:
            print(f"COMPILE_TIME:\t{t_r - t_c}")
            print(f"RUN_TIME:\t{time_after_sim - t_r}")
            print(f"TOTAL_TIME:\t{time_after_sim - time_before_sim}")
