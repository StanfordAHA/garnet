from collections import defaultdict
from hwtypes.adt import Tuple, Product
from metamapper.node import Dag, Input, Output, Combine, Select, DagNode, IODag, Constant, Sink
from metamapper.common_passes import AddID
from DagVisitor import Visitor, Transformer
from hwtypes import Bit, BitVector
from peak.mapper.utils import Unbound
from graphviz import Digraph


class CreateBuses(Visitor):
    def __init__(self, inst_info):
        self.inst_info = inst_info

    def doit(self, dag):
        self.i = 0
        self.bid_to_width = {}
        self.node_to_bid = {}
        self.netlist = defaultdict(lambda: [])
        self.run(dag)
        #Filter bid_to_width to contain only whats in self.netlist
        buses = {bid:w for bid,w in self.bid_to_width.items() if bid in self.netlist}
        return buses, self.netlist

    def create_buses(self, adt):
        if adt == Bit:
            bid = f"e{self.i}"
            self.bid_to_width[bid] = 1
            self.i += 1
            return bid
        elif adt == BitVector[16]:
            bid = f"e{self.i}"
            self.bid_to_width[bid] = 16
            self.i += 1
            return bid
        elif issubclass(adt, BitVector):
            return None
        elif issubclass(adt, Product):
            bids = {}
            for k, t in adt.field_dict.items():
                bid = self.create_buses(t)
                if bid is None:
                    continue
                assert isinstance(bid, str)
                bids[k] = bid
            return bids
        else:
            raise NotImplementedError(f"{adt}")

    def visit_Source(self, node):
        bid = self.create_buses(node.type)
        self.node_to_bid[node] = bid

    def visit_Constant(self, node):
        self.node_to_bid[node] = None

    def visit_Select(self, node):
        Visitor.generic_visit(self, node)
        child = list(node.children())[0]
        child_bid = self.node_to_bid[child]
        assert isinstance(child_bid, dict)
        assert node.field in child_bid
        bid = child_bid[node.field]
        self.node_to_bid[node] = bid
        #print(node.field)
        self.netlist[bid].append((child, node.field))

    def visit_RegisterSource(self, node):
        bid = self.create_buses(node.type)
        self.node_to_bid[node] = bid
        self.netlist[bid].append((node, "reg"))

    def visit_RegisterSink(self, node):
        Visitor.generic_visit(self, node)
        child_bid = self.node_to_bid[node.child]
        self.netlist[child_bid].append((node, "reg"))

    def generic_visit(self, node):
        Visitor.generic_visit(self, node)
        child_bids = [self.node_to_bid[child] for child in node.children()]
        if node.node_name not in self.inst_info:
            raise ValueError(f"Missing {node.node_name} in info")
        input_t = self.inst_info[node.node_name]
        
        for field, child_bid in zip(input_t.field_dict.keys(), child_bids):
            if child_bid is None:
                continue
            assert child_bid in self.netlist
            self.netlist[child_bid].append((node, field))
        if not isinstance(node, Sink):
            bid = self.create_buses(node.type)
            self.node_to_bid[node] = bid

    def visit_Combine(self, node: Combine):
        Visitor.generic_visit(self, node)
        child_bids = [self.node_to_bid[child] for child in node.children()]
        input_t = node.type
        bids = {}
        for field, child_bid in zip(input_t.field_dict.keys(), child_bids):
            if child_bid is None:
                continue
            bids[field] = child_bid
        self.node_to_bid[node] = bids

    def visit_Output(self, node: Output):
        Visitor.generic_visit(self, node)
        child_bid = self.node_to_bid[node.child]
        if node.child.field == "stencil_valid":
            port = 'f2io_1'
        else:
            port = 'f2io_16'
        self.netlist[child_bid].append((node, port))
        #for field, bid in child_bid.items():
        #    self.netlist[bid].append((node, field))


class CreateInstrs(Visitor):
    def __init__(self, inst_info):
        self.inst_info = inst_info

    def doit(self, dag: IODag):
        self.node_to_instr = {}
        self.run(dag)
        for src, sink in zip(dag.non_input_sources, dag.non_output_sinks):
            self.node_to_instr[src] = self.node_to_instr[sink]
        return self.node_to_instr


    def visit_Input(self, node):
        self.node_to_instr[node] = 1

    def visit_Output(self, node):
        Visitor.generic_visit(self, node)
        self.node_to_instr[node] = 2

    def visit_Source(self, node):
        pass

    def visit_Select(self, node):
        Visitor.generic_visit(self, node)

    def visit_Combine(self, node):
        Visitor.generic_visit(self, node)

    def visit_Constant(self, node):
        pass

    def visit_RegisterSource(self, node):
        pass

    def visit_RegisterSink(self, node):
        Visitor.generic_visit(self, node)
        self.node_to_instr[node] = 0 #TODO what is the 'instr' for a register?

    def generic_visit(self, node: DagNode):
        Visitor.generic_visit(self, node)
        if node.node_name not in self.inst_info:
            raise ValueError(f"Need info for {node.node_name}")
        adt = self.inst_info[node.node_name]
        instr_child = list(node.children())[0]
        assert isinstance(instr_child, Constant)
        self.node_to_instr[node] = instr_child.value

class CreateMetaData(Visitor):
    def doit(self, dag):
        self.node_to_md = {}
        self.run(dag)
        return self.node_to_md

    def generic_visit(self, node):
        Visitor.generic_visit(self, node)
        if hasattr(node, "_metadata_"):
            self.node_to_md[node] = node._metadata_


class CreateIDs(Visitor):
    def __init__(self, inst_info):
        self.inst_info = inst_info

    def doit(self, dag: IODag):
        self.i = 0
        self.node_to_id = {}
        self.run(dag)
        for src, sink in zip(dag.non_input_sources, dag.non_output_sinks):
            self.node_to_id[src] = self.node_to_id[sink]
        return self.node_to_id

    def visit_Source(self, node):
        pass


    def visit_Output(self, node: Output):
        Visitor.generic_visit(self, node)
        child = list(node.children())[0]
        #assert isinstance(child, Combine)
        #c_children = list(child.children())
        if "io16" in node.iname:
            is_bit = False
        else:
            is_bit = True

        if is_bit:
            id = f"i{self.i}"
            #print(node)
        else:
            id = f"I{self.i}"
        self.i += 1
        self.node_to_id[node] = id

    def visit_Select(self, node):
        Visitor.generic_visit(self, node)
        child = list(node.children())[0]
        if isinstance(child, Input):
            if node.type == Bit:
                id = f"i{self.i}"
            elif node.type == BitVector[16]:
                id = f"I{self.i}"
            else:
                raise NotImplementedError(f"{node}, {node.type}")
            self.i += 1
            self.node_to_id[child] = id

    def visit_Combine(self, node):
        Visitor.generic_visit(self, node)

    def visit_Constant(self, node):
        pass

    def visit_RegisterSource(self, node):
        pass

    def visit_RegisterSink(self, node):
        Visitor.generic_visit(self, node)
        if node.type == Bit:
            id = f"r{self.i}"
        elif node.type == BitVector[16]:
            id = f"r{self.i}"
        else:
            raise NotImplementedError(f"{node}, {node.type}")
        self.node_to_id[node] = id
        self.i += 1

    def generic_visit(self, node: DagNode):
        Visitor.generic_visit(self, node)
        if node.node_name not in self.inst_info:
            raise ValueError(f"Need info for {node.node_name}")
        id = f"{self.inst_info[node.node_name]}{self.i}"
        self.node_to_id[node] = id
        self.i += 1


def p(msg, adt):
    print(msg, list(adt.field_dict.items()))

def is_bv(adt):
    return issubclass(adt, (BitVector, Bit))

def flatten_adt(adt, path=()):
    if is_bv(adt):
        return {path: adt}
    elif issubclass(adt, Product):
        ret = {}
        for k in adt.field_dict:
            sub_ret = flatten_adt(adt[k], path + (k,))
            ret.update(sub_ret)
        return ret
    elif issubclass(adt, Tuple):
        ret = {}
        for i in range(len(adt.field_dict)):
            sub_ret = flatten_adt(adt[i], path + (i,))
            ret.update(sub_ret)
        return ret
    else:
        raise NotImplementedError(adt)


class IO_Input_t(Product):
    io2f_16=BitVector[16]
    io2f_1=Bit

class IO_Output_t(Product):
    f2io_16=BitVector[16]
    f2io_1=Bit

class FlattenIO(Visitor):
    def __init__(self):
        pass

    def doit(self, dag: Dag):
        input_t = dag.input.type
        output_t = dag.output.type
        ipath_to_type = flatten_adt(input_t)
        self.node_to_opaths = {}
        self.node_to_ipaths = {}
        self.node_map = {}
        self.opath_to_type = flatten_adt(output_t)

        isel = lambda t: "io2f_1" if t==Bit else "io2f_16"
        real_inputs = [Input(type=IO_Input_t, iname="_".join(str(field) for field in path)) for path in ipath_to_type]
        self.inputs = {path: inode.select(isel(t)) for inode, (path, t) in zip(real_inputs, ipath_to_type.items())}
        #breakpoint()
        self.outputs = {}
        self.run(dag)
        real_sources = [self.node_map[s] for s in dag.sources[1:]]
        real_sinks = [self.node_map[s] for s in dag.sinks[1:]]
        return IODag(inputs=real_inputs, outputs=self.outputs.values(), sources=real_sources, sinks=real_sinks)

    def visit_Output(self, node: Output):
        Visitor.generic_visit(self, node)
        for field, child in zip(node.type.field_dict, node.children()):
            child_paths = self.node_to_opaths[child]
            for child_path, new_child in child_paths.items():
                new_path = (field, *child_path)
                assert new_path in self.opath_to_type
                child_t = self.opath_to_type[new_path]
                if child_t == Bit:
                    combine_children = [Constant(type=BitVector[16], value=Unbound), new_child]
                else:
                    combine_children = [new_child, Constant(type=Bit, value=Unbound)]
                cnode = Combine(*combine_children, type=IO_Output_t)

                # Bad hack, read_en signals aren't actually connected to anything, this should be checked
                if "read_en" not in field:
                    self.outputs[new_path] = Output(cnode, type=IO_Output_t, iname="_".join(str(field) for field in new_path))

    def visit_Combine(self, node: Combine):
        Visitor.generic_visit(self, node)
        adt = node.type
        assert issubclass(adt, (Product, Tuple))
        paths = {}
        for k, child in zip(adt.field_dict.keys(), node.children()):
            child_paths = self.node_to_opaths[child]
            for child_path, new_child in child_paths.items():
                new_path = (k, *child_path)
                paths[new_path] = new_child
        self.node_to_opaths[node] = paths

    def visit_Select(self, node: Select):
        def get_input_node(node, path=()):
            if isinstance(node, Input):
                assert path in self.inputs
                return self.inputs[path]
            elif isinstance(node, Select):
                child = list(node.children())[0]
                return get_input_node(child, (node.field, *path))
            else:
                return None
        input_node = get_input_node(node)
        if input_node is not None:
            self.node_map[node] = input_node
            return

        Visitor.generic_visit(self, node)
        new_children = [self.node_map[child] for child in node.children()]
        new_node = node.copy()
        new_node.set_children(*new_children)
        self.node_to_opaths[node] = {(): new_node}
        self.node_map[node] = new_node

    def generic_visit(self, node: DagNode):
        Visitor.generic_visit(self, node)
        new_children = [self.node_map[child] for child in node.children()]
        new_node = node.copy()
        new_node.set_children(*new_children)
        self.node_to_opaths[node] = {(): new_node}
        self.node_map[node] = new_node



def print_netlist_info(info, filename):

    outfile = open(filename, 'w')
    print("id to instance name", file = outfile)
    for k, v in info["id_to_name"].items():
        print(f"  {k}  {v}", file = outfile)

    print("id_to_Instrs", file = outfile)
    for k, v in info["id_to_instrs"].items():
        print(f"  {k}, {v}", file = outfile)

    print("id_to_metadata", file = outfile)
    for k, v in info["id_to_metadata"].items():
        print(f"  {k}, {v}", file = outfile)

    print("buses", file = outfile)
    for k,v in info["buses"].items():
        print(f"  {k}, {v}", file = outfile)

    print("netlist", file = outfile)
    for bid, v in info["netlist"].items():
        print(f"  {bid}", file = outfile)
        for _v in v:
            print(f"    {_v}", file = outfile)
    outfile.close()

def is_unbound_const(node):
    return isinstance(node, Constant) and node.value is Unbound

class DagToPdf(Visitor):
    def __init__(self, nodes_to_ids, no_unbound):
        self.no_unbound = no_unbound
        self.nodes_to_ids = nodes_to_ids

    def doit(self, dag: Dag):
        self.graph = Digraph()
        self.run(dag)
        return self.graph

    def generic_visit(self, node):
        Visitor.generic_visit(self, node)
        def n2s(node):
            return f"{str(node)}_{str(node.iname)}"
        if self.no_unbound and not is_unbound_const(node):
            self.graph.node(n2s(node))
        for i, child in enumerate(node.children()):
            if self.no_unbound and not is_unbound_const(child):
                self.graph.edge(n2s(child), n2s(node), label=str(i))

def gen_dag_img(dag, file, info, no_unbound=True):
    DagToPdf(info, no_unbound).doit(dag).render(filename=file)


class RemoveInputsOutputs(Visitor):
    def __init__(self):
        pass

    def doit(self, dag: Dag):
        self.node_map = {}
        self.inputs = []
        self.outputs = []
        self.run(dag)
        real_sources = [self.node_map[s] for s in dag.sources[1:]]
        real_sinks = [self.node_map[s] for s in dag.sinks[1:]]
        #breakpoint()
        return IODag(inputs=self.inputs, outputs=self.outputs, sources=real_sources, sinks=real_sinks)


    def visit_Select(self, node: DagNode):
        Visitor.generic_visit(self, node)
        if not ("hw_output" in [child.iname for child in node.children()] or "self" in [child.iname for child in node.children()]):
            new_children = [self.node_map[child] for child in node.children()]
            io_child = new_children[0]
            if "io16in" in io_child.iname:
                new_node = new_children[0].select("io2f_16")
            elif "io1in" in io_child.iname:
                new_node = new_children[0].select("io2f_1")
            else:
                new_node = node.copy()
            new_node.set_children(*new_children)
            self.node_map[node] = new_node

    def generic_visit(self, node: DagNode):
        Visitor.generic_visit(self, node)
        if node.node_name == "global.IO" or node.node_name == "global.BitIO":
            if "write" in node.iname:
                new_node = Output(type=IO_Output_t, iname=node.iname)
                new_children = [self.node_map[child] for child in node.children()]
                new_node.set_children(*new_children)
                self.outputs.append(new_node)
            else:
                new_node = Input(type=IO_Input_t, iname=node.iname)
                self.inputs.append(new_node)

            self.node_map[node] = new_node
        else:
            if not(node.node_name == "Input" or "Input" in [child.node_name for child in node.children()]):
                new_children = [self.node_map[child] for child in node.children()]
                new_node = node.copy()
                new_node.set_children(*new_children)
                self.node_map[node] = new_node


class CountTiles(Visitor):
    def __init__(self):
        pass

    def doit(self, dag: Dag):
        self.num_pes = 0
        self.num_mems = 0
        self.num_ios = 0
        self.num_regs = 0
        self.run(dag)
        print(f"PEs: {self.num_pes}")
        print(f"MEMs: {self.num_mems}")
        print(f"IOs: {self.num_ios}")
        print(f"Regs: {self.num_regs}")

    def generic_visit(self, node: DagNode):
        Visitor.generic_visit(self, node)
        if node.node_name == "global.IO" or node.node_name == "global.BitIO":
            self.num_ios += 1
        elif node.node_name == "global.PE":
            self.num_pes += 1
        elif node.node_name == "global.MEM":
            self.num_mems += 1
        elif node.node_name == "coreir.reg":
            self.num_regs += 1

from lassen.sim import PE_fc as lassen_fc
from metamapper. common_passes import print_dag

def create_netlist_info(dag: Dag, tile_info: dict, load_only = False, id_to_name = None):
    gen_dag_img(dag, "dag", None)
    # Extract IO metadata
    # Inline IO tiles

    #fdag = FlattenIO().doit(dag)

    fdag = RemoveInputsOutputs().doit(dag)


    #print_dag(fdag)
    #gen_dag_img(fdag, "dag_no_io", None)

    def tile_to_char(t):
        if t.split(".")[1]=="PE":
            return "p"
        elif t.split(".")[1]=="MEM":
            return "m"
        elif t.split(".")[1] == "IO":
            return "I"
        elif t.split(".")[1] == "BitIO":
            return "i"

    node_info = {t:tile_to_char(t) for t in tile_info}
    nodes_to_ids = CreateIDs(node_info).doit(fdag)
   
    if load_only:
        name_to_id = {name:id_ for id_, name in id_to_name.items()}
        nodes_to_ids = {node:name_to_id[node.iname] for node,_ in nodes_to_ids.items()}

    info = {}
    info["id_to_name"] = {id: node.iname for node,id in nodes_to_ids.items()}

    node_to_metadata = CreateMetaData().doit(fdag)
    info["id_to_metadata"] = {nodes_to_ids[node]: md for node, md in node_to_metadata.items()}

    nodes_to_instrs = CreateInstrs(node_info).doit(fdag)
    info["id_to_instrs"] = {id:nodes_to_instrs[node] for node, id in nodes_to_ids.items()}
    
    info["instance_to_instrs"] = {node.iname:nodes_to_instrs[node] for node, id in nodes_to_ids.items() if ("p" in id or "m" in id)}
    for node, md in node_to_metadata.items():
        info["instance_to_instrs"][node.iname] = md


    node_info = {t:fc.Py.input_t for t,fc in tile_info.items()}
    bus_info, netlist = CreateBuses(node_info).doit(fdag)
    info["buses"] = bus_info
    info["netlist"] = {}
    for bid, ports in netlist.items():
        info["netlist"][bid] = [(nodes_to_ids[node], field) for node, field in ports]

    CountTiles().doit(fdag)    

    return info

