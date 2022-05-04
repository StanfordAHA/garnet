from pydot import Graph
from cgra.util import create_cgra
from memory_core.buffet_core import BuffetCore
from memory_core.fake_pe_core import FakePECore
from memory_core.intersect_core import IntersectCore
from memory_core.lookup_core import LookupCore
from memory_core.memtile_util import NetlistBuilder
from memory_core.reg_core import RegCore
from memory_core.scanner_core import ScannerCore
from memory_core.write_scanner_core import WriteScannerCore
from sam.onyx.parse_dot import *
from sam.onyx.hw_nodes.hw_node import *
from sam.onyx.hw_nodes.memory_node import MemoryNode
from sam.onyx.hw_nodes.broadcast_node import BroadcastNode
from sam.onyx.hw_nodes.compute_node import ComputeNode
from sam.onyx.hw_nodes.glb_node import GLBNode
from sam.onyx.hw_nodes.buffet_node import BuffetNode
from sam.onyx.hw_nodes.read_scanner_node import ReadScannerNode
from sam.onyx.hw_nodes.write_scanner_node import WriteScannerNode
from sam.onyx.hw_nodes.intersect_node import IntersectNode
from sam.onyx.hw_nodes.reduce_node import ReduceNode
from sam.onyx.hw_nodes.lookup_node import LookupNode
from sam.onyx.hw_nodes.merge_node import MergeNode
from sam.onyx.hw_nodes.repeat_node import RepeatNode
from sam.onyx.hw_nodes.repsiggen_node import RepSigGenNode


class SparseTBBuilder():
    def __init__(self, nlb: NetlistBuilder = None, graph: Graph = None) -> None:
        assert nlb is not None, "NLB is none..."
        assert graph is not None, "Graph is none..."

        self.nlb = nlb
        self.graph = graph
        self.core_nodes = {}

        self.register_cores()
        self.connect_cores()
        self.configure_cores()

        # Add flush connection
        flush_in = self.nlb.register_core("io_1", name="flush_in")
        self.nlb.add_connections(connections=self.nlb.emit_flush_connection(flush_in))
        # Now we have the configured CGRA...

    def register_cores(self):
        '''
        Go through each core and register it, also add it to dict of core nodes
        '''
        for node in self.graph.get_nodes():
            hw_node_type = node.get_attributes()['hwnode']
            new_node_type = None
            core_tag = None
            new_name = node.get_attributes()['label']
            print(node.get_attributes())
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
                core_tag = "scanner"
            elif hw_node_type == f"{HWNodeType.WriteScanner}":
                new_node_type = WriteScannerNode
                core_tag = "write_scanner"
            elif hw_node_type == f"{HWNodeType.Intersect}":
                new_node_type = IntersectNode
                core_tag = "intersect"
            elif hw_node_type == f"{HWNodeType.Reduce}":
                new_node_type = ReduceNode
                core_tag = "regcore"
            elif hw_node_type == f"{HWNodeType.Lookup}":
                new_node_type = LookupNode
                core_tag = "lookup"
            elif hw_node_type == f"{HWNodeType.Merge}":
                new_node_type = MergeNode
                core_tag = "intersect"
            elif hw_node_type == f"{HWNodeType.Repeat}":
                new_node_type = RepeatNode
                core_tag = "repeat"
            elif hw_node_type == f"{HWNodeType.Compute}":
                new_node_type = ComputeNode
                core_tag = "intersect"
            # elif hw_node_type == f"{HWNodeType.Broadcast}":
                # new_node = GLBNode()
            # elif hw_node_type == f"{HWNodeType.RepSigGen}":
                # new_node = GLBNode()
            else:
                raise NotImplementedError(f"{hw_node_type} not supported....")

            assert new_node_type is not None
            assert core_tag != ""
            print("MEK")
            print(node.get_attributes()['type'])
            if new_node_type == GLBNode:
                # Have to handle the GLB nodes slightly differently
                # Instead of directly registering a core, we are going to register the io,
                # connect them to the appropriate block, then instantiate and wire a
                # systemverilog wrapper of the simulation level transactions for GLB
                if node.get_attributes()['type'].strip('"') == 'fiberlookup':
                    # GLB write wants a data input, ready, valid
                    glb_name = "GLB_TO_CGRA"
                    data = self.nlb.register_core("io_16", name="data_in_")
                    ready = self.nlb.register_core("io_1", name="ready_out_")
                    valid = self.nlb.register_core("io_1", name="valid_in_")
                elif node.get_attributes()['type'].strip('"') == 'fiberwrite':
                    # GLB read wants a data output, ready, valid
                    data = self.nlb.register_core("io_16", name="data_out_")
                    ready = self.nlb.register_core("io_1", name="ready_in_")
                    valid = self.nlb.register_core("io_1", name="valid_out_")
                    glb_name = "CGRA_TO_GLB"
                elif node.get_attributes()['type'].strip('"') == 'arrayvals':
                    # GLB write wants a data input, ready, valid
                    glb_name = "GLB_TO_CGRA"
                    data = self.nlb.register_core("io_16", name="data_in_")
                    ready = self.nlb.register_core("io_1", name="ready_out_")
                    valid = self.nlb.register_core("io_1", name="valid_in_")
                else:
                    raise NotImplementedError
                self.core_nodes[node.get_name()] = GLBNode(name=glb_name, data=data, valid=valid, ready=ready)
            else:
                reg_ret = self.nlb.register_core(core_tag, flushable=True, name=new_name)
                self.core_nodes[node.get_name()] = new_node_type(name=reg_ret)


    def connect_cores(self):
        '''
        Iterate through the edges of the graph and connect each core up
        '''

        self.display_names()
        edges = self.graph.get_edges()
        for edge in edges:
            src = edge.get_source()
            dst = edge.get_destination()
            src_name = src
            dst_name = dst
            addtl_conns = self.core_nodes[src_name].connect(self.core_nodes[dst_name], edge)
            if addtl_conns is not None:
                self.nlb.add_connections(addtl_conns, defer_placement=True)


    def configure_cores(self):
        '''
        Go through nodes and configure each based on the attributes...
        '''
        for node in self.graph.get_nodes():
            node_attr = node.get_attributes()
            print(node_attr)
            node_config = self.core_nodes[node.get_name()].configure(node_attr)
            # GLB tiles return none so that we don't try to config map them...
            if node_config is not None:
                self.nlb.configure_tile(self.core_nodes[node.get_name()].get_name(), node_config)


    def display_names(self):
        self.nlb.display_names()


if __name__ == "__main__":
    matmul_dot = "/home/max/Documents/SPARSE/sam/compiler/sam-outputs/dot/" + "mat_identity.gv"
    sdg = SAMDotGraph(filename=matmul_dot)
    # Now use the graph to build an nlb
    graph = sdg.get_graph()

    chip_size = 16
    num_tracks = 5
    altcore = [ScannerCore, IntersectCore, FakePECore, RegCore, LookupCore, WriteScannerCore, BuffetCore]

    interconnect = create_cgra(width=chip_size, height=chip_size,
                               io_sides=NetlistBuilder.io_sides(),
                               num_tracks=num_tracks,
                               add_pd=True,
                               mem_ratio=(1, 2),
                               altcore=altcore)

    nlb = NetlistBuilder(interconnect=interconnect, cwd="/home/max/Documents/SPARSE/")

    stb = SparseTBBuilder(nlb=nlb, graph=graph)

    stb.display_names()