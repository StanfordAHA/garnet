import argparse
import json
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
from peak import family
from lake.modules.scanner_pipe import ScannerPipe


class SparseTBBuilder(m.Generator2):
    def __init__(self, nlb: NetlistBuilder = None, graph: Graph = None, bespoke=False,
                 input_dir=None, output_dir=None, local_mems=True,
                 mode_map=None, real_pe=False, harden_flush=False, combined=False,
                 input_sizes=None) -> None:
        assert nlb is not None or bespoke is True, "NLB is none..."
        assert graph is not None, "Graph is none..."

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

        self.input_ctr = 0
        self.output_ctr = 1

        self.glb_to_io_mapping = {}
        self.glb_cores = {}
        self._ctr = 0

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
            # src_inst = self.fabric.children[src_name]
            # dst_inst = self.fabric.children[dst_name]
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
                            #     # wire_use_src = conn_src_inst.ports[conn_src_prt]
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
                # if 'lake' in self.__cache_gens:
                #     core_inst = self.__cache_gens['lake']
                # else:
                #     core_inst = LakeTop()
                #     self.__cache_gens['lake'] = core_inst
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
            # elif hw_node_type == f"{HWNodeType.Broadcast}":
                # new_node = GLBNode()
            elif hw_node_type == f"{HWNodeType.RepSigGen}" or hw_node_type == HWNodeType.RepSigGen:
                new_node_type = RepSigGenNode
                core_name = "repeat_signal_generator"
                core_inst = RepeatSignalGenerator()
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

        self._all_dones = []

        glb_nodes = [node for node in self.core_nodes.values() if type(node) == GLBNode]
        if len(glb_nodes) < 3:
            print('STOPPING')
            exit()
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
                glb_mode = self.mode_map[glb_tensor][glb_mode_][0]
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
                print(node.get_format())
                if not node.get_format() == "dense":
                    with open(file_full, "r") as ff:
                        glb_tx_size = len(ff.readlines())
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
                    f1 = f"\"{self.output_dir}/tensor_X_mode_{glb_mode}_crd\""
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
                core_tag = "reduce"
            elif hw_node_type == f"{HWNodeType.Lookup}":
                new_node_type = LookupNode
                core_tag = "lookup"
            elif hw_node_type == f"{HWNodeType.Merge}" or hw_node_type == HWNodeType.Merge:
                new_node_type = MergeNode
                # core_tag = "intersect"
                core_tag = "crddrop"
                outer = node.get_attributes()['outer'].strip('"')
                inner = node.get_attributes()['inner'].strip('"')
                kwargs = {
                    "outer": outer,
                    "inner": inner
                }
            elif hw_node_type == f"{HWNodeType.CrdHold}" or hw_node_type == HWNodeType.CrdHold:
                new_node_type = CrdHoldNode
                # core_tag = "intersect"
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
            # elif hw_node_type == f"{HWNodeType.Broadcast}":
                # new_node = GLBNode()
            elif hw_node_type == f"{HWNodeType.RepSigGen}" or hw_node_type == HWNodeType.RepSigGen:
                new_node_type = RepSigGenNode
                # core_tag = "repeat_signal_generator"
                core_tag = "rsg"
            else:
                raise NotImplementedError(f"{hw_node_type} not supported....")

            assert new_node_type is not None
            assert core_tag != ""
            if new_node_type == GLBNode:
                glb_tensor_ = node.get_attributes()['tensor'].strip('"')
                if 'arrayvals' in node.get_attributes()['type'].strip('"'):
                    glb_mode_ = 'vals'
                else:
                    glb_mode_ = node.get_attributes()['mode'].strip('"')
                # Have to handle the GLB nodes slightly differently
                # Instead of directly registering a core, we are going to register the io,
                # connect them to the appropriate block, then instantiate and wire a
                # systemverilog wrapper of the simulation level transactions for GLB
                if node.get_attributes()['type'].strip('"') == 'fiberlookup':
                    # GLB write wants a data input, ready, valid
                    glb_name = "GLB_TO_CGRA"
                    data = self.nlb.register_core("io_16", name=f"data_in_{glb_tensor_}_{glb_mode_}")
                    # ready = self.nlb.register_core("io_1", name="ready_out_")
                    # valid = self.nlb.register_core("io_1", name="valid_in_")
                    direction = "write"
                    num_blocks = 1
                    file_number = 0
                    tx_size = 7
                    if node.get_attributes()['mode'].strip('"') == 1 or node.get_attributes()['mode'].strip('"') == '1':
                        file_number = 1
                        tx_size = 12
                    # glb_writer = m.define_from_verilog_file()
                elif node.get_attributes()['type'].strip('"') == 'fiberwrite':
                    # GLB read wants a data output, ready, valid
                    data = self.nlb.register_core("io_16", name=f"data_out_{glb_tensor_}_{glb_mode_}")
                    # ready = self.nlb.register_core("io_1", name="ready_in_")
                    # valid = self.nlb.register_core("io_1", name="valid_out_")
                    direction = "read"
                    glb_name = "CGRA_TO_GLB"
                    if 'vals' in node.get_attributes()['mode'].strip('"') or 'vals' in node.get_attributes()['format'].strip('"'):
                        num_blocks = 1
                    else:
                        num_blocks = 2
                    tx_size = 1
                elif node.get_attributes()['type'].strip('"') == 'arrayvals':
                    # GLB write wants a data input, ready, valid
                    glb_name = "GLB_TO_CGRA"
                    data = self.nlb.register_core("io_16", name=f"data_in_{glb_tensor_}_{glb_mode_}")
                    # ready = self.nlb.register_core("io_1", name="ready_out_")
                    # valid = self.nlb.register_core("io_1", name="valid_in_")
                    direction = "write"
                    num_blocks = 1
                    tx_size = 7
                    file_number = 2
                else:
                    raise NotImplementedError

                # Set tensor and mode for writing
                glb_tensor = node.get_attributes()['tensor'].strip('"')
                if 'arrayvals' in node.get_attributes()['type'].strip('"'):
                    glb_mode = 'vals'
                else:
                    glb_mode = node.get_attributes()['mode'].strip('"')

                glb_format = node.get_attributes()['format'].strip('"') if 'format' in node.get_attributes().keys() else None

                self.core_nodes[node.get_name()] = GLBNode(name=data,
                                                           data=data,
                                                           valid=None,
                                                           # valid=valid,
                                                           ready=None,
                                                           # ready=ready,
                                                           direction=direction,
                                                           num_blocks=num_blocks,
                                                           file_number=file_number,
                                                           tx_size=tx_size,
                                                           tensor=glb_tensor,
                                                           mode=glb_mode,
                                                           format=glb_format)

                self.glb_to_io_mapping[data] = (glb_tensor, glb_mode, direction, num_blocks)

                if direction == "write":
                    self.glb_cores[data] = (self.input_ctr, 0)
                    self.input_ctr += 2
                else:
                    self.glb_cores[data] = (self.output_ctr, 0)
                    self.output_ctr += 2

            else:
                reg_ret = self.nlb.register_core(core_tag, flushable=True, name=new_name)
                self.core_nodes[node.get_name()] = new_node_type(name=reg_ret, **kwargs)

    def get_glb_mapping(self):
        return self.glb_to_io_mapping

    def connect_cores(self):
        '''
        Iterate through the edges of the graph and connect each core up
        '''
        edges = self.graph.get_edges()
        for edge in edges:
            src = edge.get_source()
            dst = edge.get_destination()
            src_name = src
            dst_name = dst

            # print(src)
            # print(dst)

            addtl_conns = self.core_nodes[src_name].connect(self.core_nodes[dst_name], edge)
            # Remap the pe connections
            # if self.real_pe:
            #     real_pe_tag = 'f'
            #     real_pe_remap = {
            #         'data_out': 'res',
            #         'data_in_0': 'data0',
            #         'data_in_1': 'data1'
            #     }

            #     for conn_block_name, sig_struct in addtl_conns.items():
            #         for i, complex_sig in enumerate(sig_struct):
            #             sig_list, width = complex_sig
            #             for idx, sig_tuple in enumerate(sig_list):
            #                 prim_name, prim_sig = sig_tuple
            #                 if prim_name[0] == real_pe_tag:
            #                     print("Remapping f...")
            #                     sig_list[idx] = (prim_name, real_pe_remap[prim_sig])

            if addtl_conns is not None:
                self.nlb.add_connections(addtl_conns, defer_placement=True)

        # exit()

    def configure_cores(self):
        '''
        Go through nodes and configure each based on the attributes...
        '''
        for node in self.graph.get_nodes():
            node_attr = node.get_attributes()
            node_config_ret = self.core_nodes[node.get_name()].configure(node_attr)
            print(node_config_ret)
            if node_config_ret is not None:
                node_config_tuple, node_config_kwargs = node_config_ret
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
                    print("SAW GLB...skipping")
                    # self.nlb.configure_tile(self.core_nodes[node.get_name()].get_name(), node_config_tuple)
                    # continue
                print(f"Node name --- {self.core_nodes[node.get_name()].get_name()}")
                # Hack for now - identify core combiner nodes and pass them the kwargs
                if "m" in self.core_nodes[node.get_name()].get_name() or "p" in self.core_nodes[node.get_name()].get_name():
                    runtime_modes = self.nlb.get_core_runtimes()
                    runtime_mode = runtime_modes[self.core_nodes[node.get_name()].get_name()]
                    # Now need to set the runtime
                    node_config_kwargs['mode'] = runtime_mode
                    pass_config_kwargs_tuple = (1, node_config_kwargs)
                    self.nlb.configure_tile(self.core_nodes[node.get_name()].get_name(), pass_config_kwargs_tuple)
                # elif "s" in self.core_nodes[node.get_name()].get_name():
                else:
                    print(node.get_name(), self.core_nodes[node.get_name()].get_name())
                    if "glb" in node.get_name():
                        node_config_kwargs['sparse_mode'] = 1
                    self.nlb.configure_tile(self.core_nodes[node.get_name()].get_name(), (1, node_config_kwargs))
                # else:
                    # print(node.get_name(), self.core_nodes[node.get_name()].get_name())
                    # self.nlb.configure_tile(self.core_nodes[node.get_name()].get_name(), node_config_tuple)

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


def prepare_glb_collateral(glb_dir=None, bitstream=None, matrices_in=None, design_place=None, glb_info=None):

    assert glb_dir is not None
    assert bitstream is not None
    assert matrices_in is not None
    assert design_place is not None
    assert glb_info is not None

    # Call this when ready for it
    if not os.path.exists(glb_dir):
        os.mkdir(glb_dir)
    if not os.path.exists(f"{glb_dir}/bin"):
        os.mkdir(f"{glb_dir}/bin")

    input_glb_tiles = [glb_tile for glb_tile in glb_info if glb_tile[3] == 'write']
    output_glb_tiles = [glb_tile for glb_tile in glb_info if glb_tile[3] == 'read']

    print(input_glb_tiles)
    print(output_glb_tiles)

    # input_glb_tiles_ = []
    # output_glb_tiles_ = []

    # Loop through the input matrices and create raw versions
    # for filename in os.listdir(matrices_in):
    for idx_, input_glb_tile in enumerate(input_glb_tiles):
        (core, core_placement, tensor_desc_str, direction, num_blocks) = input_glb_tile
        assert os.path.exists(f"{matrices_in}/{tensor_desc_str}")
        # ret = os.remove(matrices_in + "/" + filename)
        os.system(f"xxd -r -p {matrices_in}/{tensor_desc_str} > {glb_dir}/bin/{tensor_desc_str}.raw")
        with open(f"{matrices_in}/{tensor_desc_str}") as tmp_fp:
            num_lines = len(tmp_fp.readlines())
        # num_lines = os.system(f"wc -l {matrices_in}/{filename}")
        # print(filename)
        # print("NUM LINES")
        # print(f"{num_lines}")
        input_glb_tiles[idx_] = (core, core_placement, tensor_desc_str, num_lines, num_blocks)

    shutil.copyfile(bitstream, f"{glb_dir}/bin/bitstream.bs")
    shutil.copyfile(design_place, f"{glb_dir}/bin/design.place")

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
        "placement": "design.place"
    }
    design_meta_json["IOs"] = {
        "inputs": [],
        "outputs": []
    }

    tmp_json = None
    for input_glb_tile in input_glb_tiles:
        (core, core_placement, tensor_desc_str, num_lines, num_blocks) = input_glb_tile
        tmp_json = {
            "bitwidth": 16,
            "datafile": f"{tensor_desc_str}.raw",
            "name": tensor_desc_str,
            "shape": [num_lines],
            "io_tiles": [
                {
                    "name": tensor_desc_str,
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
        # print("MEK")
        # print(design_meta_json["IOs"]["inputs"])
        design_meta_json["IOs"]["inputs"].append(tmp_json)
        # print(design_meta_json["IOs"]["inputs"])

    for idx_, output_glb_tile in enumerate(output_glb_tiles):
        (core, core_placement, tensor_desc_str, direction, num_blocks) = output_glb_tile
        assert os.path.exists(f"{glb_dir}/{tensor_desc_str}")
        # ret = os.remove(matrices_in + "/" + filename)
        os.system(f"xxd -r -p {glb_dir}/{tensor_desc_str} > {glb_dir}/bin/{tensor_desc_str}.raw")
        with open(f"{glb_dir}/{tensor_desc_str}") as tmp_fp:
            num_lines = len(tmp_fp.readlines())
        # num_lines = os.system(f"wc -l {matrices_in}/{filename}")
        # print(filename)
        # print("NUM LINES")
        # print(f"{num_lines}")
        output_glb_tiles[idx_] = (core, core_placement, tensor_desc_str, num_lines, num_blocks)

    tmp_json = None
    for output_glb_tile in output_glb_tiles:
        (core, core_placement, tensor_desc_str, num_lines, num_blocks) = output_glb_tile
        tmp_json = {
            "bitwidth": 16,
            "datafile": f"{tensor_desc_str}.raw",
            "name": tensor_desc_str,
            "shape": [num_lines],
            "io_tiles": [
                {
                    "name": tensor_desc_str,
                    "mode": "RV",
                    "num_blocks": num_blocks,
                    "addr": {
                        "cycle_starting_addr": [0],
                        "cycle_stride": [1],
                        "dimensionality": 1,
                        "extent": [num_lines],
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


def write_glb_file(file_list, out_dir, out_name):

    output_lines = []

    for f in file_list:
        with open(f, 'r') as curr_file:
            all_lines = curr_file.readlines()
            # Get rid of 0x for readmemh compatibility
            # hexified = str(hex(len(all_lines)))[2:]
            output_lines.append(f"{len(all_lines):04X}\n")
            for l in all_lines:
                # Get rid of 0x for readmemh compatibility
                # hexified = str(hex(int(l)))[2:]
                output_lines.append(f"{int(l):04X}\n")
    out_path = f"{out_dir}/{out_name}"
    with open(out_path, "w+") as curr_file:
        curr_file.writelines(output_lines)


def coalesce_files(in_dir, out_dir):
    # First, find the unique guys in the in_dir (tensors)
    tensors = {}
    all_in_files = os.listdir(in_dir)
    for fname in all_in_files:
        if "shape" in fname:
            continue
        tname = fname.split("_")[1]
        if tname not in tensors:
            tensors[tname] = 1
    for tname, _ in tensors.items():
        # Assume everything CSF right now - always a seg/crd array
        mode_num = 0
        done = False
        while done is False:
            if f'tensor_{tname}_mode_{mode_num}_seg' in all_in_files:
                # Found it...
                # Now coalesce the seg/crd into a single file
                write_glb_file([f'{in_dir}/tensor_{tname}_mode_{mode_num}_seg',
                               f'{in_dir}/tensor_{tname}_mode_{mode_num}_crd'],
                               out_dir=out_dir, out_name=f'tensor_{tname}_mode_{mode_num}')
                mode_num = mode_num + 1
            else:
                done = True
        # Now do vals
        write_glb_file([f'{in_dir}/tensor_{tname}_mode_vals'], out_dir=out_dir, out_name=f'tensor_{tname}_mode_vals')


def software_gold(app_name, matrix_tmp_dir, give_tensor=False, print_inputs=None):

    output_matrix = None
    output_format = None

    input_tensors = dict()

    b_mat = None
    c_mat = None
    d_mat = None

    output_name = None
    input_dims = {}

    if 'mat_elemadd.gv' in app_name:
        # PASSES
        # to glb
        # combined
        if give_tensor:
            bshape = read_inputs(os.path.join(matrix_tmp_dir, "Bshape"))
            cshape = read_inputs(os.path.join(matrix_tmp_dir, "Cshape"))
            b_matrix = get_tensor_from_files(name='B', files_dir=matrix_tmp_dir, shape=bshape, base=10, early_terminate='x')
            c_matrix = get_tensor_from_files(name='C', files_dir=matrix_tmp_dir, shape=cshape, base=10, early_terminate='x')
        else:
            shape_ = 10
            b_matrix = MatrixGenerator(name="B", shape=[shape_, shape_], sparsity=0.7, format='CSF', dump_dir=matrix_tmp_dir)
            c_matrix = MatrixGenerator(name="C", shape=[shape_, shape_], sparsity=0.7, format='CSF', dump_dir=matrix_tmp_dir)
            b_matrix.dump_outputs()
            c_matrix.dump_outputs()

        b_mat = b_matrix.get_matrix()
        c_mat = c_matrix.get_matrix()

        output_matrix = numpy.add(b_mat, c_mat, dtype=numpy.uint16, casting='unsafe')
        output_format = "CSF"
        output_name = "X"
    elif 'mat_elemadd3.gv' in app_name:
        # PASSES
        # to glb
        # combined
        # piped
        shape_ = 10
        b_matrix = MatrixGenerator(name="B", shape=[shape_, shape_], sparsity=0.7, format='CSF', dump_dir=matrix_tmp_dir)
        c_matrix = MatrixGenerator(name="C", shape=[shape_, shape_], sparsity=0.7, format='CSF', dump_dir=matrix_tmp_dir)
        d_matrix = MatrixGenerator(name="D", shape=[shape_, shape_], sparsity=0.7, format='CSF', dump_dir=matrix_tmp_dir)
        b_matrix.dump_outputs()
        c_matrix.dump_outputs()
        d_matrix.dump_outputs()
        b_mat = b_matrix.get_matrix()
        c_mat = c_matrix.get_matrix()
        d_mat = d_matrix.get_matrix()

        output_matrix = numpy.add(d_mat, numpy.add(b_mat, c_mat,
                                                   dtype=numpy.uint16, casting='unsafe'), dtype=numpy.uint16, casting='unsafe')
        output_format = "CSF"
        output_name = "X"
    elif 'mat_elemmul.gv' in app_name:
        # PASSES
        # to glb
        # combined
        # piped
        b_matrix = MatrixGenerator(name="B", shape=[10, 10], sparsity=0.7, format='CSF', dump_dir=matrix_tmp_dir)
        c_matrix = MatrixGenerator(name="C", shape=[10, 10], sparsity=0.7, format='CSF', dump_dir=matrix_tmp_dir)
        b_matrix.dump_outputs()
        c_matrix.dump_outputs()
        b_mat = b_matrix.get_matrix()
        c_mat = c_matrix.get_matrix()
        output_matrix = numpy.multiply(b_mat, c_mat, dtype=numpy.uint16, casting='unsafe')
        output_format = "CSF"
        output_name = "X"
    elif 'mat_identity.gv' in app_name:
        # PASSES
        # to glb
        # combined
        # piped
        shape_ = 40
        b_matrix = MatrixGenerator(name="B", shape=[shape_, shape_], sparsity=0.7, format='CSF', dump_dir=matrix_tmp_dir)
        b_matrix.dump_outputs()
        b_mat = b_matrix.get_matrix()
        output_matrix = b_mat
        output_format = "CSF"
        output_name = "X"
    elif 'mat_identity_dense.gv' in app_name:
        # PASSES
        # TODO: Deal with no files for dense
        b_matrix = MatrixGenerator(name="B", shape=[10, 10], sparsity=0.7, format='UNC', dump_dir=matrix_tmp_dir)
        b_matrix.dump_outputs()
        b_mat = b_matrix.get_matrix()
        output_matrix = b_mat
        output_format = "UNC"
        output_name = "X"
    elif 'mat_mattransmul.gv' in app_name:
        # WRONG GRAPH
        raise NotImplementedError
        b_matrix = MatrixGenerator(name="b", shape=[1], sparsity=0.7, format='CSF', dump_dir=matrix_tmp_dir)
    elif 'mat_residual.gv' in app_name:
        # WRONG GRAPH
        shape_ = 10
        b_matrix = MatrixGenerator(name="b", shape=[shape_], sparsity=0.7, format='CSF', dump_dir=matrix_tmp_dir)
        C_matrix = MatrixGenerator(name="C", shape=[shape_, shape_], sparsity=0.7, format='CSF', dump_dir=matrix_tmp_dir)
        d_matrix = MatrixGenerator(name="d", shape=[shape_], sparsity=0.7, format='CSF', dump_dir=matrix_tmp_dir)
        b_matrix.dump_outputs()
        C_matrix.dump_outputs()
        d_matrix.dump_outputs()
        b_mat = b_matrix.get_matrix()
        C_mat = C_matrix.get_matrix()
        d_mat = d_matrix.get_matrix()
        output_matrix = numpy.subtract(b_mat,
                                       numpy.matmul(C_mat, d_mat, dtype=numpy.uint16, casting='unsafe'),
                                       dtype=numpy.uint16, casting='unsafe')
        output_format = "CSF"
        output_name = "x"
        # raise NotImplementedError
    elif 'mat_sddmm.gv' in app_name:
        shape_ = 4
        b_matrix = MatrixGenerator(name="B", shape=[shape_, shape_], sparsity=0.7, format='CSF', dump_dir=matrix_tmp_dir)
        c_matrix = MatrixGenerator(name="C", shape=[shape_, shape_], sparsity=0.7, format='UNC', dump_dir=matrix_tmp_dir)
        d_matrix = MatrixGenerator(name="D", shape=[shape_, shape_], sparsity=0.7, format='UNC', dump_dir=matrix_tmp_dir)
        b_matrix.dump_outputs()
        c_matrix.dump_outputs()
        d_matrix.dump_outputs()
        input_dims[b_matrix.get_name()] = tuple(b_matrix.get_shape())
        input_dims[c_matrix.get_name()] = tuple(c_matrix.get_shape())
        input_dims[d_matrix.get_name()] = tuple(d_matrix.get_shape())
        b_mat = b_matrix.get_matrix()
        c_mat = c_matrix.get_matrix()
        d_mat = d_matrix.get_matrix()
        d_mat_trans = numpy.transpose(d_mat)
        # exit()
        # First transpose c_mat
        tmp = numpy.matmul(c_mat, d_mat_trans, dtype=numpy.uint16, casting='unsafe')
        output_matrix = numpy.multiply(b_mat, tmp, dtype=numpy.uint16, casting='unsafe')
        output_format = "CSF"
        output_name = "X"
        # raise NotImplementedError
    elif 'mat_vecmul_ij.gv' in app_name:
        # PASSES
        # to glb
        # combined
        # piped
        b_matrix = MatrixGenerator(name="B", shape=[10, 10], sparsity=0.7, format='CSF', dump_dir=matrix_tmp_dir)
        c_matrix = MatrixGenerator(name="c", shape=[10], sparsity=0.7, format='CSF', dump_dir=matrix_tmp_dir)
        b_matrix.dump_outputs()
        c_matrix.dump_outputs()
        b_mat = b_matrix.get_matrix()
        c_mat = c_matrix.get_matrix()
        # First transpose c_mat
        c_mat_trans = numpy.transpose(c_mat)
        output_matrix = numpy.matmul(b_mat, c_mat_trans, dtype=numpy.uint16, casting='unsafe')
        output_format = "CSF"
        output_name = "x"
    elif 'mat_vecmul_ji.gv' in app_name:
        raise NotImplementedError
    elif 'matmul_ijk.gv' in app_name:
        # PASSES
        # to glb
        # combined
        # piped
        if give_tensor:
            bshape = read_inputs(os.path.join(matrix_tmp_dir, "Bshape"))
            cshape = read_inputs(os.path.join(matrix_tmp_dir, "Cshape"))
            b_matrix = get_tensor_from_files(name='B', files_dir=matrix_tmp_dir, shape=bshape, base=10, early_terminate='x')
            c_matrix = get_tensor_from_files(name='C', files_dir=matrix_tmp_dir, shape=cshape, base=10, early_terminate='x')
        else:
            gold_shape_ = 20
            b_matrix = MatrixGenerator(name="B", shape=[gold_shape_, gold_shape_], sparsity=0.7, format='CSF', dump_dir=matrix_tmp_dir)
            c_matrix = MatrixGenerator(name="C", shape=[gold_shape_, gold_shape_], sparsity=0.7, format='CSF', dump_dir=matrix_tmp_dir)
            b_matrix.dump_outputs()
            c_matrix.dump_outputs()
        b_mat = b_matrix.get_matrix()
        c_mat = c_matrix.get_matrix()
        # First transpose c_mat
        c_mat_trans = numpy.transpose(c_mat)
        output_matrix = numpy.matmul(b_mat, c_mat_trans, dtype=numpy.uint16, casting='unsafe')
        output_format = "CSF"
        output_name = "X"
    elif 'matmul_ikj.gv' in app_name:
        raise NotImplementedError
        b_matrix = MatrixGenerator(name="B", shape=[10, 10], sparsity=0.7, format='CSF', dump_dir=matrix_tmp_dir)
        c_matrix = MatrixGenerator(name="C", shape=[10, 10], sparsity=0.7, format='CSF', dump_dir=matrix_tmp_dir)
        b_matrix.dump_outputs()
        c_matrix.dump_outputs()
        b_mat = b_matrix.get_matrix()
        c_mat = c_matrix.get_matrix()
        # First transpose c_mat
        c_mat_trans = numpy.transpose(c_mat)
        output_matrix = numpy.matmul(b_mat, c_mat_trans)
        output_name = "X"
    elif 'matmul_jik.gv' in app_name:
        # PASSED
        # to glb
        # combined
        # piped
        b_matrix = MatrixGenerator(name="B", shape=[10, 10], sparsity=0.7, format='CSF', dump_dir=matrix_tmp_dir)
        c_matrix = MatrixGenerator(name="C", shape=[10, 10], sparsity=0.7, format='CSF', dump_dir=matrix_tmp_dir)
        b_matrix.dump_outputs()
        c_matrix.dump_outputs()
        b_mat = b_matrix.get_matrix()
        c_mat = c_matrix.get_matrix()
        # First transpose c_mat
        c_mat_trans = numpy.transpose(c_mat)
        output_matrix = numpy.matmul(b_mat, c_mat_trans, dtype=numpy.uint16, casting='unsafe')
        output_matrix = numpy.transpose(output_matrix)
        output_format = "CSF"
        output_name = "X"
    elif 'matmul_jki.gv' in app_name:
        raise NotImplementedError
        b_matrix = MatrixGenerator(name="B", shape=[10, 10], sparsity=0.7, format='CSF', dump_dir=matrix_tmp_dir)
        c_matrix = MatrixGenerator(name="C", shape=[10, 10], sparsity=0.7, format='CSF', dump_dir=matrix_tmp_dir)
        b_matrix.dump_outputs()
        c_matrix.dump_outputs()
        b_mat = b_matrix.get_matrix()
        c_mat = c_matrix.get_matrix()
        # First transpose c_mat
        c_mat_trans = numpy.transpose(c_mat)
        output_matrix = numpy.matmul(b_mat, c_mat_trans)
        output_name = "X"
    elif 'matmul_kij.gv' in app_name:
        raise NotImplementedError
        b_matrix = MatrixGenerator(name="B", shape=[10, 10], sparsity=0.7, format='CSF', dump_dir=matrix_tmp_dir)
        c_matrix = MatrixGenerator(name="C", shape=[10, 10], sparsity=0.7, format='CSF', dump_dir=matrix_tmp_dir)
        b_matrix.dump_outputs()
        c_matrix.dump_outputs()
        b_mat = b_matrix.get_matrix()
        c_mat = c_matrix.get_matrix()
        # First transpose c_mat
        c_mat_trans = numpy.transpose(c_mat)
        output_matrix = numpy.matmul(b_mat, c_mat_trans)
        output_name = "X"
    elif 'matmul_kji.gv' in app_name:
        raise NotImplementedError
        b_matrix = MatrixGenerator(name="B", shape=[10, 10], sparsity=0.7, format='CSF', dump_dir=matrix_tmp_dir)
        c_matrix = MatrixGenerator(name="C", shape=[10, 10], sparsity=0.7, format='CSF', dump_dir=matrix_tmp_dir)
        b_matrix.dump_outputs()
        c_matrix.dump_outputs()
        b_mat = b_matrix.get_matrix()
        c_mat = c_matrix.get_matrix()
        # First transpose c_mat
        c_mat_trans = numpy.transpose(c_mat)
        output_matrix = numpy.matmul(b_mat, c_mat_trans)
        output_name = "X"
    elif 'tensor3_elemadd.gv' in app_name:
        # PASSES
        # to glb
        # combined
        # piped
        shape_ = 10
        b_matrix = MatrixGenerator(name="B", shape=[shape_, shape_, shape_], sparsity=0.7, format='CSF', dump_dir=matrix_tmp_dir)
        c_matrix = MatrixGenerator(name="C", shape=[shape_, shape_, shape_], sparsity=0.7, format='CSF', dump_dir=matrix_tmp_dir)
        b_matrix.dump_outputs()
        c_matrix.dump_outputs()
        b_mat = b_matrix.get_matrix()
        c_mat = c_matrix.get_matrix()
        # First transpose c_mat
        output_matrix = numpy.add(c_mat, b_mat, dtype=numpy.uint16, casting='unsafe')
        output_format = "CSF"
        output_name = "X"
    elif 'tensor3_elemmul.gv' in app_name:
        # PASSES

        # combined
        # piped
        shape_ = 10
        b_matrix = MatrixGenerator(name="B", shape=[shape_, shape_, shape_], sparsity=0.7, format='CSF', dump_dir=matrix_tmp_dir)
        c_matrix = MatrixGenerator(name="C", shape=[shape_, shape_, shape_], sparsity=0.7, format='CSF', dump_dir=matrix_tmp_dir)
        b_matrix.dump_outputs()
        c_matrix.dump_outputs()
        b_mat = b_matrix.get_matrix()
        c_mat = c_matrix.get_matrix()
        # First transpose c_mat
        output_matrix = numpy.multiply(c_mat, b_mat, dtype=numpy.uint16, casting='unsafe')
        output_format = "CSF"
        output_name = "X"
    elif 'tensor3_identity.gv' in app_name:
        # PASSES
        # separate
        # combined
        # piped
        b_matrix = MatrixGenerator(name="B", shape=[10, 10, 10], sparsity=0.7, format='CSF', dump_dir=matrix_tmp_dir)
        b_matrix.dump_outputs()
        b_mat = b_matrix.get_matrix()
        # First transpose c_mat
        output_matrix = b_mat
        output_format = "CSF"
        output_name = "X"
    elif 'tensor3_innerprod.gv' in app_name:
        # PASSES
        # separate
        # combined
        # piped
        shape_ = 10
        b_matrix = MatrixGenerator(name="B", shape=[shape_, shape_, shape_], sparsity=0.7, format='CSF', dump_dir=matrix_tmp_dir)
        c_matrix = MatrixGenerator(name="C", shape=[shape_, shape_, shape_], sparsity=0.7, format='CSF', dump_dir=matrix_tmp_dir)
        b_matrix.dump_outputs()
        c_matrix.dump_outputs()
        b_mat = b_matrix.get_matrix()
        c_mat = c_matrix.get_matrix()
        output_matrix = numpy.zeros([1])
        output_matrix[0] = numpy.sum(numpy.multiply(c_mat, b_mat, dtype=numpy.uint16, casting='unsafe'), dtype=numpy.uint16)
        output_matrix = output_matrix.astype(numpy.uint16)
        output_format = "CSF"
        output_name = "x"
    elif 'tensor3_mttkrp.gv' in app_name:
        shape_ = 10
        b_matrix = MatrixGenerator(name="B", shape=[shape_, shape_, shape_],
                                   sparsity=0.7, format='CSF', dump_dir=matrix_tmp_dir)
        c_matrix = MatrixGenerator(name="C", shape=[shape_, shape_], sparsity=0.7, format='CSF', dump_dir=matrix_tmp_dir)
        d_matrix = MatrixGenerator(name="D", shape=[shape_, shape_], sparsity=0.7, format='CSF', dump_dir=matrix_tmp_dir)
        b_matrix.dump_outputs()
        c_matrix.dump_outputs()
        d_matrix.dump_outputs()
        b_mat = b_matrix.get_matrix()
        c_mat = c_matrix.get_matrix()
        d_mat = d_matrix.get_matrix()
        c_mat_trans = numpy.transpose(c_mat)
        d_mat_trans = numpy.transpose(d_mat)
        print(repr(b_mat))
        print(repr(c_mat_trans))
        print(repr(d_mat_trans))
        output_matrix = numpy.einsum("ikl,lj,kj->ij", b_mat, d_mat_trans, c_mat_trans, dtype=numpy.uint16, casting='unsafe')
        # output_matrix = numpy.einsum("ikl,jl,jk->ij", b_mat, d_mat, c_mat, dtype=numpy.uint16, casting='unsafe')

        output_format = "CSF"
        output_name = "X"
    elif 'tensor3_ttm.gv' in app_name:
        shape_ = 4
        b_matrix = MatrixGenerator(name="B", shape=[shape_, shape_, shape_], sparsity=0.7, format='CSF', dump_dir=matrix_tmp_dir)
        c_matrix = MatrixGenerator(name="C", shape=[shape_, shape_], sparsity=0.7, format='CSF', dump_dir=matrix_tmp_dir)
        print(b_matrix)
        print(c_matrix)
        b_matrix.dump_outputs()
        c_matrix.dump_outputs()
        b_mat = b_matrix.get_matrix()
        c_mat = c_matrix.get_matrix()
        c_mat_trans = numpy.transpose(c_mat)
        # First transpose c_mat
        output_matrix = numpy.matmul(b_mat, c_mat_trans, dtype=numpy.uint16, casting='unsafe')
        output_format = "CSF"
        output_name = "X"
    elif 'tensor3_ttv.gv' in app_name:
        shape_ = 10
        b_matrix = MatrixGenerator(name="B", shape=[shape_, shape_, shape_], sparsity=0.7, format='CSF', dump_dir=matrix_tmp_dir)
        c_matrix = MatrixGenerator(name="c", shape=[shape_], sparsity=0.7, format='CSF', dump_dir=matrix_tmp_dir)
        b_matrix.dump_outputs()
        c_matrix.dump_outputs()
        b_mat = b_matrix.get_matrix()
        c_mat = c_matrix.get_matrix()
        # First transpose c_mat
        output_matrix = numpy.matmul(b_mat, c_mat, dtype=numpy.uint16, casting='unsafe')
        output_format = "CSF"
        output_name = "X"
    elif 'vec_elemadd.gv' in app_name:
        # PASSES
        # separate
        # combined
        # piped
        shape_ = 50
        b_matrix = MatrixGenerator(name="b", shape=[shape_], sparsity=0.7, format='CSF', dump_dir=matrix_tmp_dir)
        c_matrix = MatrixGenerator(name="c", shape=[shape_], sparsity=0.7, format='CSF', dump_dir=matrix_tmp_dir)
        b_matrix.dump_outputs()
        c_matrix.dump_outputs()
        b_mat = b_matrix.get_matrix()
        c_mat = c_matrix.get_matrix()
        # First transpose c_mat
        output_matrix = numpy.add(c_mat, b_mat, dtype=numpy.uint16, casting='unsafe')
        output_format = "CSF"
        output_name = "x"
    elif 'vec_elemmul.gv' in app_name:
        # PASSES
        # separate
        # combined
        # piped
        b_matrix = MatrixGenerator(name="b", shape=[50], sparsity=0.7, format='CSF', dump_dir=matrix_tmp_dir)
        c_matrix = MatrixGenerator(name="c", shape=[50], sparsity=0.7, format='CSF', dump_dir=matrix_tmp_dir)
        b_matrix.dump_outputs()
        c_matrix.dump_outputs()
        b_mat = b_matrix.get_matrix()
        c_mat = c_matrix.get_matrix()
        # First transpose c_mat
        output_matrix = numpy.multiply(c_mat, b_mat, dtype=numpy.uint16, casting='unsafe')
        output_format = "CSF"
        output_name = "x"
    elif 'vec_identity.gv' in app_name:
        # PASSES
        # separate
        # combined
        # piped
        b_matrix = MatrixGenerator(name="b", shape=[100], sparsity=0.7, format='CSF', dump_dir=matrix_tmp_dir)
        b_matrix.dump_outputs()
        b_mat = b_matrix.get_matrix()
        output_matrix = b_mat
        output_format = "CSF"
        output_name = "x"
    elif 'vec_scalar_mul.gv' in app_name:
        # PASSES
        # separate
        # combined
        # piped
        b_matrix = MatrixGenerator(name="b", shape=[1], sparsity=0.7, format='CSF', dump_dir=matrix_tmp_dir)
        c_matrix = MatrixGenerator(name="c", shape=[10], sparsity=0.7, format='CSF', dump_dir=matrix_tmp_dir)
        b_matrix.dump_outputs()
        c_matrix.dump_outputs()
        b_mat = b_matrix.get_matrix()
        c_mat = c_matrix.get_matrix()
        output_matrix = numpy.multiply(c_mat, b_mat, dtype=numpy.uint16, casting='unsafe')
        output_format = "CSF"
        output_name = "x"
    elif 'mat_identity_crdhold' in app_name:
        b_matrix = MatrixGenerator(name="B", shape=[10, 10], sparsity=0.7, format='CSF', dump_dir=matrix_tmp_dir)
        b_matrix.dump_outputs()
        b_mat = b_matrix.get_matrix()
        output_matrix = b_mat
        output_format = "COO"
    else:
        raise NotImplementedError

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

    return output_matrix, output_format, output_name, input_dims


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Sparse TB Generator')
    parser.add_argument('--sam_graph',
                        type=str,
                        default="/home/max/Documents/SPARSE/sam/compiler/sam-outputs/dot/mat_identity.gv")
    parser.add_argument('--output_dir',
                        type=str,
                        default="/home/max/Documents/SPARSE/garnet/mek_outputs")
    parser.add_argument('--input_dir',
                        type=str,
                        default="/Users/maxwellstrange/Documents/SPARSE/garnet/final_matrix_inputs")
    parser.add_argument('--test_dump_dir',
                        type=str,
                        default="/home/max/Documents/SPARSE/garnet/mek_dump/")
    parser.add_argument('--matrix_tmp_dir',
                        type=str,
                        default="/Users/maxwellstrange/Documents/SPARSE/garnet/tmp_matrix_inputs")
    parser.add_argument('--gold_dir',
                        type=str,
                        default="/Users/maxwellstrange/Documents/SPARSE/garnet/gold_out")
    parser.add_argument('--print_inputs',
                        type=str,
                        default=None)
    parser.add_argument('--fifo_depth',
                        type=int,
                        default=8)
    parser.add_argument('--seed', type=int, default=0)
    parser.add_argument('--height', type=int, default=16)
    parser.add_argument('--width', type=int, default=16)
    parser.add_argument('--trace', action="store_true")
    parser.add_argument('--bespoke', action="store_true")
    parser.add_argument('--remote_mems', action="store_true")
    parser.add_argument('--ic_fork', action="store_true")
    parser.add_argument('--give_tensor', action="store_true")
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
    parser.add_argument('--glb_dir',
                        type=str,
                        default="/home/max/Documents/SPARSE/garnet/GLB_DIR")
    args = parser.parse_args()
    bespoke = args.bespoke
    output_dir = args.output_dir
    input_dir = args.input_dir
    use_fork = args.ic_fork
    matrix_tmp_dir = args.matrix_tmp_dir
    seed = args.seed
    test_dump_dir = args.test_dump_dir
    gold_dir = args.gold_dir
    give_tensor = args.give_tensor
    fifo_depth = args.fifo_depth
    physical_sram = args.physical_sram
    just_verilog = args.just_verilog
    clk_enable = args.clk_enable
    gen_pe = args.gen_pe
    add_pond = args.add_pond
    combined = args.combined
    sam_graph = args.sam_graph
    pipeline_scanner = args.pipeline_scanner
    dump_bitstream = args.dump_bitstream
    harden_flush = not args.no_harden_flush
    print_inputs = args.print_inputs
    dump_glb = args.dump_glb
    glb_dir = args.glb_dir
    chip_h = args.height
    chip_w = args.width

    # Make sure to force DISABLE_GP for much quicker runs
    os.environ['DISABLE_GP'] = '1'

    pe_prefix = "PEGEN_"
    real_pe = False

    # Create PE verilog for inclusion...
    if gen_pe is True:
        pe_child = PE_fc(family.MagmaFamily())
        m.compile(f"{args.test_dump_dir}/PE", pe_child, output="coreir-verilog", coreir_libs={"float_CW"}, verilog_prefix=pe_prefix)
        m.clear_cachedFunctions()
        m.frontend.coreir_.ResetCoreIR()
        m.generator.reset_generator_cache()
        m.logging.flush_all()  # flush all staged logs

    numpy.random.seed(seed)
    random.seed(seed)

    nlb = None
    interconnect = None
    if bespoke is False:
        # chip_width = 20
        chip_width = 20
        # chip_height = 32
        chip_height = 16
        num_tracks = 5

        controllers = []

        if pipeline_scanner:
            scan = ScannerPipe(data_width=16,
                               fifo_depth=fifo_depth,
                               add_clk_enable=True,
                               defer_fifos=True,
                               add_flush=False)
        else:
            scan = Scanner(data_width=16,
                           fifo_depth=fifo_depth,
                           defer_fifos=True,
                           add_flush=False)

        wscan = WriteScanner(data_width=16, fifo_depth=fifo_depth,
                             defer_fifos=True,
                             add_flush=False)
        strg_ub = StrgUBVec(data_width=16, mem_width=64, mem_depth=512)
        fiber_access = FiberAccess(data_width=16,
                                   local_memory=False,
                                   tech_map=GF_Tech_Map(depth=512, width=32),
                                   defer_fifos=True)
        buffet = BuffetLike(data_width=16, mem_depth=512, local_memory=False,
                            tech_map=GF_Tech_Map(depth=512, width=32),
                            defer_fifos=True,
                            optimize_wide=True,
                            add_flush=False)
        strg_ram = StrgRAM(data_width=16,
                           banks=1,
                           memory_width=64,
                           memory_depth=512,
                           rw_same_cycle=False,
                           read_delay=1,
                           addr_width=16,
                           prioritize_write=True,
                           comply_with_17=True)

        stencil_valid = StencilValid()

        controllers.append(scan)
        controllers.append(wscan)
        controllers.append(buffet)
        controllers.append(strg_ub)
        # controllers.append(fiber_access)
        controllers.append(strg_ram)
        controllers.append(stencil_valid)

        isect = Intersect(data_width=16,
                          use_merger=False,
                          fifo_depth=8,
                          defer_fifos=True,
                          add_flush=False)
        crd_drop = CrdDrop(data_width=16, fifo_depth=fifo_depth,
                           lift_config=True,
                           defer_fifos=True,
                           add_flush=False)
        crd_hold = CrdHold(data_width=16, fifo_depth=fifo_depth,
                           lift_config=True,
                           defer_fifos=True,
                           add_flush=False)
        onyxpe = OnyxPE(data_width=16, fifo_depth=fifo_depth, defer_fifos=True,
                        ext_pe_prefix=pe_prefix,
                        pe_ro=True,
                        do_config_lift=False,
                        add_flush=False)
        repeat = Repeat(data_width=16,
                        fifo_depth=8,
                        defer_fifos=True,
                        add_flush=False)
        rsg = RepeatSignalGenerator(data_width=16,
                                    passthru=False,
                                    fifo_depth=fifo_depth,
                                    defer_fifos=True,
                                    add_flush=False)
        regcr = Reg(data_width=16,
                    fifo_depth=fifo_depth,
                    defer_fifos=True,
                    add_flush=False)

        controllers_2 = []

        controllers_2.append(isect)
        controllers_2.append(crd_drop)
        controllers_2.append(crd_hold)
        controllers_2.append(onyxpe)
        controllers_2.append(repeat)
        controllers_2.append(rsg)
        controllers_2.append(regcr)

        if combined is True:
            altcore = [(CoreCombinerCore, {'controllers_list': controllers_2,
                                           'use_sim_sram': not physical_sram,
                                           'tech_map': GF_Tech_Map(depth=512, width=32),
                                           'pnr_tag': "p",
                                           'name': "PE",
                                           'input_prefix': "PE_"}),
                       (CoreCombinerCore, {'controllers_list': controllers_2,
                                           'use_sim_sram': not physical_sram,
                                           'tech_map': GF_Tech_Map(depth=512, width=32),
                                           'pnr_tag': "p",
                                           'name': "PE",
                                           'input_prefix': "PE_"}),
                       (CoreCombinerCore, {'controllers_list': controllers_2,
                                           'use_sim_sram': not physical_sram,
                                           'tech_map': GF_Tech_Map(depth=512, width=32),
                                           'pnr_tag': "p",
                                           'name': "PE",
                                           'input_prefix': "PE_"}),
                       (CoreCombinerCore, {'controllers_list': controllers,
                                           'use_sim_sram': not physical_sram,
                                           'tech_map': GF_Tech_Map(depth=512, width=32),
                                           'pnr_tag': "m",
                                           'name': "MemCore",
                                           'input_prefix': "MEM_"})]
            # altcore = [(CoreCombinerCore, {'controllers_list': controllers,
            #                                'use_sim_sram': not physical_sram,
            #                                'tech_map': GF_Tech_Map(depth=512, width=32),
            #                                'pnr_tag': "C",
            #                                'name': "MemCore",
            #                                'input_prefix': "MEM_"}),
            #            (CoreCombinerCore, {'controllers_list': controllers_2,
            #                                'use_sim_sram': not physical_sram,
            #                                'tech_map': GF_Tech_Map(depth=512, width=32),
            #                                'pnr_tag': "Q",
            #                                'name': "PE",
            #                                'input_prefix': "PE_"})]
            real_pe = True

        else:
            altcore = [(ScannerCore, {'fifo_depth': fifo_depth,
                                      'add_clk_enable': clk_enable,
                                      'pipelined': pipeline_scanner}),
                       (BuffetCore, {'local_mems': True,
                                     'physical_mem': physical_sram,
                                     'fifo_depth': fifo_depth,
                                     'tech_map': GF_Tech_Map(depth=512, width=32)}),
                       (OnyxPECore, {'fifo_depth': fifo_depth, 'ext_pe_prefix': pe_prefix}),
                       (WriteScannerCore, {'fifo_depth': fifo_depth}),
                       (RepeatCore, {'fifo_depth': fifo_depth}),
                       (IntersectCore, {'fifo_depth': fifo_depth}),
                       (CrdDropCore, {'fifo_depth': fifo_depth}),
                       (CrdHoldCore, {'fifo_depth': fifo_depth}),
                       (RepeatSignalGeneratorCore, {'passthru': not use_fork,
                                                    'fifo_depth': fifo_depth}),
                       (RegCore, {'fifo_depth': fifo_depth})]

            real_pe = True

        interconnect = create_cgra(width=chip_width, height=chip_height,
                                   io_sides=IOSide.North,
                                   num_tracks=num_tracks,
                                   add_pd=False,
                                   # Soften the flush...?
                                   harden_flush=harden_flush,
                                   altcore=altcore,
                                   ready_valid=True,
                                   add_pond=add_pond)

        if just_verilog:
            circuit = interconnect.circuit()
            import magma
            magma.compile(f"{test_dump_dir}/SparseTBBuilder", circuit, coreir_libs={"float_CW"})
            exit()

        nlb = NetlistBuilder(interconnect=interconnect, cwd=test_dump_dir,
                             harden_flush=harden_flush, combined=combined)

    ##### Handling app level file stuff #####
    output_matrix, output_format, output_name, input_dims = software_gold(sam_graph, matrix_tmp_dir, give_tensor, print_inputs)
    out_mat = MatrixGenerator(name=output_name, shape=None, sparsity=0.5, format=output_format, dump_dir=gold_dir, tensor=output_matrix)
    out_mat.dump_outputs()
    if dump_glb:

        # Make sure glb path exists
        if not os.path.isdir(glb_dir):
            os.mkdir(glb_dir)

        out_mat.dump_outputs(glb_override=True, glb_dump_dir=glb_dir)

    # Now coalesce them into combo files and put in final landing zone
    # First clear the out dir
    if not os.path.isdir(input_dir):
        os.mkdir(input_dir)
    else:
        # Otherwise clean it
        for filename in os.listdir(input_dir):
            ret = os.remove(input_dir + "/" + filename)
    coalesce_files(in_dir=matrix_tmp_dir, out_dir=input_dir)

    # Clean up output dir...
    # If it doesn't exist, make it
    if not os.path.isdir(output_dir):
        os.mkdir(output_dir)
    else:
        # Otherwise clean it
        for filename in os.listdir(output_dir):
            ret = os.remove(output_dir + "/" + filename)

    # Get SAM graph
    # sdg = SAMDotGraph(filename=args.sam_graph, local_mems=not args.remote_mems, use_fork=use_fork)
    sdg = SAMDotGraph(filename=args.sam_graph, local_mems=True, use_fork=use_fork)
    mode_map = sdg.get_mode_map()
    print(f"MODE MAP: {mode_map}")
    # exit()
    graph = sdg.get_graph()

    print(input_dims)
    ##### Create the actual testbench mapping based on the SAM graph #####
    stb = SparseTBBuilder(nlb=nlb, graph=graph, bespoke=bespoke, input_dir=input_dir,
                          # output_dir=output_dir, local_mems=not args.remote_mems, mode_map=tuple(mode_map.items()))
                          output_dir=output_dir, local_mems=True, mode_map=tuple(mode_map.items()),
                          real_pe=real_pe, harden_flush=harden_flush, combined=combined,
                          input_sizes=tuple(input_dims.items()))

    if dump_bitstream:
        nlb.write_out_bitstream(f"{test_dump_dir}/bitstream.bs")

    if dump_glb:

        glb_info_ = []
        glb_map = stb.get_glb_mapping()
        mode_map = stb.get_mode_map()
        for core, desc_ in glb_map.items():
            tensor_, mode_, direction_, num_blocks_ = desc_
            # remap the mode...
            if mode_ != 'vals':
                mode_ = mode_map[tensor_][int(mode_)][0]
            print(core)
            core_placement = stb.get_core_placement(core)
            print(core_placement)
            tensor_desc_str = f"tensor_{tensor_}_mode_{mode_}"
            print(tensor_desc_str)
            glb_info_.append((core, core_placement, tensor_desc_str, direction_, num_blocks_))

        prepare_glb_collateral(glb_dir=glb_dir,
                               bitstream=f"{test_dump_dir}/bitstream.bs",
                               matrices_in=input_dir,
                               design_place=f"{test_dump_dir}/design.place",
                               glb_info=glb_info_)

    stb.display_names()
    stb.dump_display_names(f"{test_dump_dir}/design.mapped")

    ##### Create the actual testbench #####
    tester = BasicTester(stb, stb.clk, stb.rst_n)

    tester.zero_inputs()
    tester.poke(stb.io.stall, 1)
    tester.poke(stb.io.rst_n, 0)
    tester.eval()

    tester.step(2)
    tester.poke(stb.rst_n, 1)

    # if nlb is not None:
    #     tester.reset()
    # else:
    #     # pulse reset manually
    #     tester.poke(stb.rst_n, 0)
    #     tester.step(2)
    #     tester.poke(stb.rst_n, 1)
    #     tester.step(2)

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
    # tester.poke(stb.io.flush, 1)
    # tester.eval()
    tester.step(2)
    tester.step(2)
    # tester.step(2)
    # tester.step(2)
    # tester.step(2)
    # for i in range(1000):
    #     tester.step(2)
    tester.poke(stb.io.flush, 0)
    tester.eval()
    # for i in range(100000):
    for i in range(50000):
        tester.step(2)
        tester_if = tester._if(tester.circuit.done)
        tester_if.print("Test is done...\n")
        tester_if.print("Cycle Count...%d\n", stb.io.cycle_count)
        tester_if.finish()
    # tester.wait_until_high(tester.circuit.done, timeout=2000)

    from conftest import run_tb_fn
    run_tb_fn(tester, trace=args.trace, disable_ndarray=False, cwd=test_dump_dir, include_PE=True)
    # run_tb_fn(tester, trace=True, disable_ndarray=True, cwd="./")

    stb.display_names()

    ##### Now check it... #####
    print(f"GOLD")
    print(output_matrix)

    sim_mat = get_tensor_from_files(name='X', files_dir=output_dir,
                                    format=output_format, shape=output_matrix.shape, base=16, early_terminate='x')
    sim_mat_np = sim_mat.get_matrix()
    print(f"SIM")
    print(sim_mat_np)

    assert numpy.array_equal(output_matrix, sim_mat_np)
