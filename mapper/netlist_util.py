from collections import defaultdict
from hwtypes.adt import Tuple, Product
from metamapper.node import Dag, Input, Output, Combine, Select, DagNode, IODag, Constant, Sink
from metamapper.common_passes import AddID
from DagVisitor import Visitor
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
        assert isinstance(child_bid, dict)
        for field, bid in child_bid.items():
            self.netlist[bid].append((node, field))


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
        assert isinstance(child, Combine)
        c_children = list(child.children())
        if isinstance(c_children[0], Constant):
            is_bit = True
        else:
            is_bit = False

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



class PlacementHelper(Visitor):
    def __init__(self):
        pass
    def doit(self, dag: IODag):
        self.pe_paths = []
        self.run(dag)
        for path in self.pe_paths:
            path.reverse()
        return self.pe_paths
    def generic_visit(self, node: DagNode):
        if node.node_name == "global.PE":
            found = False
            for path in self.pe_paths:
                if node.iname in path:
                    found = True
                    break
            if not found:
                path = []
                path.append(node.iname)
                self.pe_paths.append(path)
            for child in node.children():
                print(child)
                for chil in child.children():
                    if chil.node_name == "global.PE":
                        path.append(chil.iname)
        Visitor.generic_visit(self, node)



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
        AddID().run(dag)
        self.graph = Digraph()
        self.run(dag)
        return self.graph

    def generic_visit(self, node):
        Visitor.generic_visit(self, node)
        def n2s(node):
            return f"{str(node)}_{node._id_}"
        if self.no_unbound and not is_unbound_const(node):
            if node in self.nodes_to_ids:
                self.graph.node(n2s(node), label=self.nodes_to_ids[node])
            else:
                self.graph.node(n2s(node))
        for i, child in enumerate(node.children()):
            if self.no_unbound and not is_unbound_const(child):
                self.graph.edge(n2s(child), n2s(node), label=str(i))

def gen_dag_img(dag, file, info, no_unbound=True):
    DagToPdf(info, no_unbound).doit(dag).render(filename=file)

from lassen.sim import PE_fc as lassen_fc
from metamapper. common_passes import print_dag

def create_netlist_info(dag: Dag, tile_info: dict, load_only = False, id_to_name = None):
    fdag = FlattenIO().doit(dag)
    # gen_dag_img(fdag, f"img/foo")
    def tile_to_char(t):
        if t.split(".")[1]=="PE":
            return "p"
        elif t.split(".")[1]=="MEM":
            return "m"
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

    return info
    #gen_dag_img(fdag, "placement_dag", nodes_to_ids)

    paths = PlacementHelper().doit(fdag)

    placements = []
    placed_tiles = set()

    pe_x = 0

    ic = 30
    oc = 30
    output_mem_y = 20
    grid_x = 64
    grid_y = 24

    for bid, tiles in info["netlist"].items():
        if len(tiles) == ic + 1:
            input_y = -1
            pe_name = None
            pe_added = False
            for tile in tiles:
                if tile[0] not in placed_tiles:
                    placed_tiles.add(tile[0])
                    if 'm' in tile[0]:
                        mem_placement = {}
                        mem_placement["name"] = info["id_to_name"][tile[0]]
                        mem_placement["id"] = tile[0]
                        mem_placement["x"] = 3
                        mem_placement["y"] = input_y
                        placements.append(mem_placement)
                    elif 'p' in tile[0]:
                        pe_added = True
                        pe_placement = {}
                        pe_placement["name"] = info["id_to_name"][tile[0]]
                        pe_placement["id"] = tile[0]
                        pe_placement["x"] = pe_x
                        if (pe_x + 2) % 4 != 0:
                            pe_x += 1
                        else:
                            pe_x += 2
                        pe_placement["y"] = input_y
                        placements.append(pe_placement)
                    else:
                        print("Error, not pe or mem tile")
                    # print(tile[0])
                pe_name = info["id_to_name"][tile[0]]

            for path in paths:
                if pe_name in path:
                    input_y = path.index(pe_name) 
            print(input_y + 1)
            if pe_added:
                for placement in placements:
                    if placement["y"] == -1:
                        placement["y"] = (input_y + 1)
            else:
                for placement in placements:
                    if placement["y"] == -1:
                        placement["y"] = (input_y + 1)
                        placement["x"] = 7

            pe_x = 0
        
    mem_x = 11
    mem_y = 1
    for idx, (id, name) in enumerate(info["id_to_name"].items()): 
        if id not in placed_tiles:
            if "m" in id and "conv_stencil$ub_conv_stencil_BANK" in name:
                mem_placement = {}
                mem_placement["name"] = name
                mem_placement["id"] = id
                mem_placement["x"] = mem_x
                mem_placement["y"] = mem_y
                if mem_y >= grid_y:
                    mem_y = 1
                    mem_x += 4
                else:
                    mem_y += 1
                placements.append(mem_placement)
                # print(mem_placement)


    pe_x = 1
    pe_y = 18
    mem_x = 19
    mem_y = 1

    io_x_in = 0
    io_x_out = 1
    bit_io_x_in = 0
    bit_io_x_out = 1

    last_idx = -1
    for idx, (id, name) in enumerate(info["id_to_name"].items()): 
        if id not in placed_tiles:
            if "p" in id:
                pe_placement = {}
                pe_placement["name"] = name
                pe_placement["id"] = id
                pe_placement["x"] = pe_x
                if (pe_x + 2) % 4 != 0:
                    pe_x += 1
                else:
                    pe_x += 2
                if pe_x >= 40:
                    pe_y += 1
                    pe_x = 1
                pe_placement["y"] = pe_y
                placements.append(pe_placement)
                last_idx = idx
            elif "m" in id:
                mem_placement = {}
                mem_placement["name"] = name
                mem_placement["id"] = id
                mem_placement["x"] = mem_x
                mem_placement["y"] = mem_y
                if mem_y >= output_mem_y - 1:
                    mem_y = 1
                    mem_x += 4
                else:
                    mem_y += 1
                placements.append(mem_placement)
            elif "I" in id:
                io_placement = {}
                io_placement["name"] = name
                io_placement["id"] = id
                io_placement["y"] = 0
                if "input" in name:
                    io_placement["x"] = io_x_in
                    io_x_in += 2
                else:
                    io_placement["x"] = io_x_out
                    io_x_out += 2
                placements.append(io_placement)
            elif "i" in id:
                io_placement = {}
                io_placement["name"] = name
                io_placement["id"] = id
                io_placement["y"] = 0
                if "input" in name or "reset" in name:
                    io_placement["x"] = bit_io_x_in
                    bit_io_x_in += 2
                else:
                    io_placement["x"] = bit_io_x_out
                    bit_io_x_out += 2
                placements.append(io_placement)
            placed_tiles.add(id)


    used_tiles = set()

    outfile = open("resnet_one_input_dse_large/design.place", 'w')
    print("Block Name \t X \t Y \t #Block ID", file = outfile)
    print("---------------------------", file = outfile)
    for p in placements:
        if (p['x'], p['y']) in used_tiles and "i" not in p["id"] and "I" not in p["id"]:
            print("Tile used twice:", p['x'], p['y'])
            print(p)
        used_tiles.add((p['x'], p['y']))
        print(f"{p['name']}\t{p['x']}\t{p['y']}\t#{p['id']}", file = outfile)

    outfile.close()

    # breakpoint()

    return info

