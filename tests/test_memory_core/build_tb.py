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
from sam.onyx.hw_node import *


class SparseTBBuilder():
    def __init__(self, nlb: NetlistBuilder = None, graph: Graph = None) -> None:
        assert nlb is not None, "NLB is none..."
        assert graph is not None, "Graph is none..."

        self.nlb = nlb
        self.graph = graph
        self.core_nodes = {}

        self.register_cores()
        self.connect_cores()

    def register_cores(self):
        '''
        Go through each core and register it, also add it to dict of core nodes
        '''
        for node in self.graph.get_nodes():
            hw_node_type = node.get_attributes()['hwnode']
            new_node = None
            core_tag = None
            new_name = node.get_attributes()['label']
            if hw_node_type == f"{HWNodeType.GLB}":
                new_node = GLBNode(name=new_name)
                core_tag = "glb"
            elif hw_node_type == f"{HWNodeType.Buffet}":
                new_node = BuffetNode(name=new_name)
                core_tag = "buffet"
            elif hw_node_type == f"{HWNodeType.Memory}":
                new_node = MemoryNode(name=new_name)
                core_tag = "memtile"
            elif hw_node_type == f"{HWNodeType.ReadScanner}":
                new_node = ReadScannerNode(name=new_name)
                core_tag = "scanner"
            elif hw_node_type == f"{HWNodeType.WriteScanner}":
                new_node = WriteScannerNode(name=new_name)
                core_tag = "write_scanner"
            elif hw_node_type == f"{HWNodeType.Intersect}":
                new_node = IntersectNode(name=new_name)
                core_tag = "intersect"
            elif hw_node_type == f"{HWNodeType.Reduce}":
                new_node = ReduceNode(name=new_name)
                core_tag = "regcore"
            elif hw_node_type == f"{HWNodeType.Lookup}":
                new_node = LookupNode(name=new_name)
                core_tag = "lookup"
            elif hw_node_type == f"{HWNodeType.Merge}":
                new_node = MergeNode(name=new_name)
                core_tag = "intersect"
            elif hw_node_type == f"{HWNodeType.Repeat}":
                new_node = RepeatNode(name=new_name)
                core_tag = "repeat"
            elif hw_node_type == f"{HWNodeType.Compute}":
                new_node = ComputeNode(name=new_name)
                core_tag = "intersect"
            # elif hw_node_type == f"{HWNodeType.Broadcast}":
                # new_node = GLBNode()
            # elif hw_node_type == f"{HWNodeType.RepSigGen}":
                # new_node = GLBNode()
            else:
                raise NotImplementedError(f"{hw_node_type} not supported....")

            assert new_node is not None
            assert core_tag != ""
            self.core_nodes[node.get_name()] = new_node
            self.nlb.register_core(core_tag, flushable=True, name=new_name)


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
            addtl_conns = self.core_nodes[src_name].connect(self.core_nodes[dst_name])
            self.nlb.add_connections(addtl_conns)


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