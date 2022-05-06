from gemstone.common.testers import BasicTester
from gemstone.common.configurable import ConfigurationType
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
import magma as m


class SparseTBBuilder(m.Generator2):
    def __init__(self, nlb: NetlistBuilder = None, graph: Graph = None) -> None:
        assert nlb is not None, "NLB is none..."
        assert graph is not None, "Graph is none..."

        self.nlb = nlb
        self.graph = graph
        self.core_nodes = {}

        self._ctr = 0

        self.io = m.IO(
            clk=m.In(m.Clock),
            rst_n=m.In(m.AsyncReset),
            stall=m.In(m.Bit),
            flush=m.In(m.Bit),
            config=m.In(ConfigurationType(32, 32))
        )

        self.register_cores()
        self.connect_cores()
        self.configure_cores()

        # self.config = self.io.config

        # Add flush connection
        flush_in = self.nlb.register_core("io_1", name="flush_in")
        self.nlb.add_connections(connections=self.nlb.emit_flush_connection(flush_in))
        # Now we have the configured CGRA...
        self.nlb.finalize_config()

        # Now attach global buffers based on placement...
        # Get circuit
        self.interconnect_circuit = self.nlb.get_circuit()
        self.interconnect_circuit = self.interconnect_circuit()

        flush_h = self.nlb.get_handle(flush_in, prefix="glb2io_1_")

        m.wire(self.interconnect_circuit['clk'], self.io.clk)
        m.wire(self.io.rst_n, self.interconnect_circuit['reset'])
        m.wire(self.io.stall, self.interconnect_circuit['stall'][0])
        # m.wire(self.io.flush, self.interconnect_circuit['flush'][0])
        print(str(flush_h))
        m.wire(self.io.flush, self.interconnect_circuit[str(flush_h)][0])

        m.wire(self.interconnect_circuit.config, self.io.config)

        # Get the initial list of inputs to interconnect and cross them off
        self.interconnect_ins = self.get_interconnect_ins()
        # Make sure to remove the flush port or it will get grounded.
        self.interconnect_ins.remove(str(flush_h))

        # self.nlb.get_route_config()

        self.attach_glb()
        self.wire_interconnect_ins()

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
        # print(all_ports)
        for port in all_ports:
            # print(port)
            if 'glb2io' in port:
                in_list.append(port)

        return in_list

    def wire_interconnect_ins(self):
        '''
        Here we are going to wire all of the relevant interconnect inputs to 0
        '''
        for ic_in in self.interconnect_ins:
            # Get width from name
            width = int(ic_in.split("_")[1])
            m.wire(self.interconnect_circuit[ic_in], m.Bits[width](0))

    def attach_glb(self):

        self._all_dones = []

        glb_nodes = [node for node in self.core_nodes.values() if type(node) == GLBNode]
        print(glb_nodes)
        if len(glb_nodes) < 3:
            print('STOPPING')
            exit()
        for node in glb_nodes:
            # Now we can realize and connect the glb nodes based on the placement
            glb_data = node.get_data()
            glb_ready = node.get_ready()
            glb_valid = node.get_valid()

            # Get the handle for these pins, then instantiate glb
            glb_dir = node.get_direction()
            if glb_dir == 'write':

                data_h = self.nlb.get_handle(glb_data, prefix="glb2io_16_")
                ready_h = self.nlb.get_handle(glb_ready, prefix="io2glb_1_")
                valid_h = self.nlb.get_handle(glb_valid, prefix="glb2io_1_")

                # Get rid of these signals from leftover inputs...
                self.interconnect_ins.remove(str(data_h))
                self.interconnect_ins.remove(str(valid_h))

                data_h = self.interconnect_circuit[str(data_h)]
                ready_h = self.interconnect_circuit[str(ready_h)]
                valid_h = self.interconnect_circuit[str(valid_h)]

                glb_type_map = {
                    "clk": m.In(m.Clock),
                    "rst_n": m.In(m.AsyncReset),
                    "data": m.Out(m.Bits[16]),
                    "ready": m.In(m.Bit),
                    "valid": m.Out(m.Bit),
                    "done": m.Out(m.Bit),
                    "flush": m.In(m.Bit)
                }

                test_glb = m.define_from_verilog_file('/home/max/Documents/SPARSE/garnet/tests/test_memory_core/glb_write.sv',
                                                      type_map=glb_type_map)[0]
                test_glb = test_glb(TX_SIZE=10)

                # m.wire(test_glb['data'], data_h)
                # m.wire(ready_h, test_glb['ready'])
                # m.wire(test_glb['valid'], valid_h)
                m.wire(test_glb['data'], data_h)
                m.wire(ready_h[0], test_glb['ready'])
                m.wire(test_glb['valid'], valid_h[0])
                m.wire(test_glb.clk, self.io.clk)
                m.wire(test_glb.rst_n, self.io.rst_n)
                m.wire(test_glb.flush, self.io.flush)

            elif glb_dir == 'read':
                data_h = self.nlb.get_handle(glb_data, prefix="io2glb_16_")
                ready_h = self.nlb.get_handle(glb_ready, prefix="glb2io_1_")
                valid_h = self.nlb.get_handle(glb_valid, prefix="io2glb_1_")

                # Get rid of this signal from leftover inputs...
                self.interconnect_ins.remove(str(ready_h))

                data_h = self.interconnect_circuit[str(data_h)]
                ready_h = self.interconnect_circuit[str(ready_h)]
                valid_h = self.interconnect_circuit[str(valid_h)]

                glb_type_map = {
                    "clk": m.In(m.Clock),
                    "rst_n": m.In(m.AsyncReset),
                    "data": m.In(m.Bits[16]),
                    "ready": m.Out(m.Bit),
                    "valid": m.In(m.Bit),
                    "done": m.Out(m.Bit),
                    "flush": m.In(m.Bit)
                }

                test_glb = m.define_from_verilog_file('/home/max/Documents/SPARSE/garnet/tests/test_memory_core/glb_read.sv',
                                                      type_map=glb_type_map)[0]
                # test_glb = m.define_from_verilog_file('./glb_read.sv')[0]
                # test_glb = test_glb()
                test_glb = test_glb(NUM_BLOCKS=1)

                m.wire(data_h, test_glb['data'])
                m.wire(test_glb['ready'], ready_h[0])
                m.wire(valid_h[0], test_glb['valid'])
                m.wire(test_glb.clk, self.io.clk)
                m.wire(test_glb.rst_n, self.io.rst_n)
                m.wire(test_glb.flush, self.io.flush)
            else:
                raise NotImplementedError(f"glb_dir was {glb_dir}")

    def register_cores(self):
        '''
        Go through each core and register it, also add it to dict of core nodes
        '''
        for node in self.graph.get_nodes():
            hw_node_type = node.get_attributes()['hwnode']
            new_node_type = None
            core_tag = None
            new_name = node.get_attributes()['label']
            # print(node.get_attributes())
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
            # print(node.get_attributes()['type'])
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
                    direction = "write"
                    # glb_writer = m.define_from_verilog_file()
                elif node.get_attributes()['type'].strip('"') == 'fiberwrite':
                    # GLB read wants a data output, ready, valid
                    data = self.nlb.register_core("io_16", name="data_out_")
                    ready = self.nlb.register_core("io_1", name="ready_in_")
                    valid = self.nlb.register_core("io_1", name="valid_out_")
                    direction = "read"
                    glb_name = "CGRA_TO_GLB"
                elif node.get_attributes()['type'].strip('"') == 'arrayvals':
                    # GLB write wants a data input, ready, valid
                    glb_name = "GLB_TO_CGRA"
                    data = self.nlb.register_core("io_16", name="data_in_")
                    ready = self.nlb.register_core("io_1", name="ready_out_")
                    valid = self.nlb.register_core("io_1", name="valid_in_")
                    direction = "write"
                else:
                    raise NotImplementedError
                self.core_nodes[node.get_name()] = GLBNode(name=glb_name, data=data, valid=valid, ready=ready, direction=direction)
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
            # print(node_attr)
            node_config = self.core_nodes[node.get_name()].configure(node_attr)
            # GLB tiles return none so that we don't try to config map them...
            if node_config is not None:
                self.nlb.configure_tile(self.core_nodes[node.get_name()].get_name(), node_config)

    def display_names(self):
        self.nlb.display_names()


if __name__ == "__main__":

    # class TestCode(m.Generator2):
    #     def __init__(self) -> None:
    #         test_glb = m.define_from_verilog_file('/home/max/Documents/SPARSE/garnet/tests/test_memory_core/glb_read.sv')
    #         test_glb = test_glb[0]
    #         print(test_glb)
    #         test_glb = test_glb()
    #         print(test_glb)

    # tc = TestCode()

    # exit()

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
                               # Soften the flush...?
                               harden_flush=False,
                               mem_ratio=(1, 2),
                               altcore=altcore)

    nlb = NetlistBuilder(interconnect=interconnect, cwd="/home/max/Documents/SPARSE/garnet/mek_dump/")

    stb = SparseTBBuilder(nlb=nlb, graph=graph)

    stb.display_names()

    interconnect.dump_pnr(dir_name="/home/max/Documents/SPARSE/garnet/mek_dump/", design_name="matrix_identity")

    # h_flush_in = nlb.get_handle(flush_in, prefix="glb2io_1_")
    # stall_in = nlb.get_handle_str("stall")

    # tester = nlb.get_tester()
    tester = BasicTester(stb, stb.clk, stb.rst_n)

    tester.reset()
    tester.zero_inputs()

    # Stall during config
    tester.poke(stb.io.stall, 1)

    # After stalling, we can configure the circuit
    # with its configuration bitstream
    cfgdat = nlb.get_config_data()
    for addr, index in cfgdat:
        tester.configure(addr, index)
        # if readback is True:
        #     self._tester.config_read(addr)
        tester.eval()

    tester.done_config()

    tester.poke(stb.io.stall, 0)
    tester.eval()

    # Get flush handle and apply flush to start off app
    tester.poke(stb.io.flush, 1)
    tester.eval()
    tester.step(2)
    tester.step(2)
    # tester.step(2)
    # tester.step(2)
    # tester.step(2)
    # for i in range(1000):
    #     tester.step(2)
    tester.poke(stb.io.flush, 0)
    tester.eval()

    from conftest import run_tb_fn
    run_tb_fn(tester, trace=True, disable_ndarray=True, cwd="mek_dump")
    # run_tb_fn(tester, trace=True, disable_ndarray=True, cwd="./")
