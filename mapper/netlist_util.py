import os, math, re
from graphviz import Digraph
from collections import defaultdict
from hwtypes import Bit, BitVector
from hwtypes.adt import Tuple, Product
from metamapper.node import (
    Dag,
    Input,
    Output,
    Combine,
    Select,
    DagNode,
    IODag,
    Constant,
    Sink,
    Common,
)
from metamapper.common_passes import AddID, print_dag, gen_dag_img
from DagVisitor import Visitor, Transformer
from peak.mapper.utils import Unbound
from lassen.sim import PE_fc as lassen_fc
from mapper.netlist_graph import Node, NetlistGraph


class CreateBuses(Visitor):
    def __init__(self, inst_info):
        self.inst_info = inst_info

    def doit(self, dag):
        self.i = 1
        self.bid_to_width = {}
        self.node_to_bid = {}
        self.netlist = defaultdict(lambda: [])
        self.run(dag)
        # Filter bid_to_width to contain only whats in self.netlist
        buses = {bid: w for bid, w in self.bid_to_width.items() if bid in self.netlist}
        return buses, self.netlist

    def create_buses(self, adt):
        if adt == Bit:
            bid = f"e{self.i}"
            self.bid_to_width[bid] = 1
            self.i += 1
            return bid
        elif adt == BitVector[16]:
            bid = f"e{self.i}"
            self.bid_to_width[bid] = 17
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
        if node.child.type == Bit:
            port = "f2io_1"
        else:
            port = "f2io_17"
        self.netlist[child_bid].append((node, port))


class CreateInstrs(Visitor):
    def __init__(self, inst_info):
        self.inst_info = inst_info

    def doit(self, dag: IODag):
        self.node_to_instr = {}
        self.run(dag)
        for src, sink in zip(dag.non_input_sources, dag.non_output_sinks):
            self.node_to_instr[src.iname] = self.node_to_instr[sink.iname]
        return self.node_to_instr

    def visit_Input(self, node):
        self.node_to_instr[node.iname] = (1,)

    def visit_Output(self, node):
        Visitor.generic_visit(self, node)
        self.node_to_instr[node.iname] = (2,)

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
        self.node_to_instr[node.iname] = 0  # TODO what is the 'instr' for a register?

    def generic_visit(self, node: DagNode):
        Visitor.generic_visit(self, node)
        if node.node_name not in self.inst_info:
            raise ValueError(f"Need info for {node.node_name}")
        adt = self.inst_info[node.node_name]
        for instr_child in node.children():
            if isinstance(instr_child, Constant):
                break

        assert isinstance(
            instr_child, Constant
        ), f"{node.node_name} {node.iname} {instr_child.node_name}"
        self.node_to_instr[node.iname] = instr_child.value


class CreateMetaData(Visitor):
    def doit(self, dag):
        self.node_to_md = {}
        self.run(dag)
        return self.node_to_md

    def generic_visit(self, node):
        Visitor.generic_visit(self, node)
        if hasattr(node, "_metadata_"):
            self.node_to_md[node.iname] = node._metadata_

class CreateIDs(Visitor):
    def __init__(self, inst_info):
        self.inst_info = inst_info

    def doit(self, dag: IODag):
        self.i = 0
        self.node_to_id = {}
        self.run(dag)
        return self.node_to_id

    def visit_Source(self, node):
        pass

    def visit_Output(self, node: Output):
        Visitor.generic_visit(self, node)
        child = list(node.children())[0]

        if "io16" in node.iname:
            id = f"I{self.i}"
        else:
            id = f"i{self.i}"
        self.i += 1
        self.node_to_id[node.iname] = id

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
            self.node_to_id[child.iname] = id

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
        self.node_to_id[node.iname] = id
        self.i += 1

    def generic_visit(self, node: DagNode):
        Visitor.generic_visit(self, node)
        if node.node_name not in self.inst_info:
            raise ValueError(f"Need info for {node.node_name}")
        id = f"{self.inst_info[node.node_name]}{self.i}"
        self.node_to_id[node.iname] = id
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
    io2f_17 = BitVector[16]
    io2f_1 = Bit


class IO_Output_t(Product):
    f2io_16 = BitVector[16]
    f2io_1 = Bit


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

        isel = lambda t: "io2f_1" if t == Bit else "io2f_17"
        real_inputs = [
            Input(type=IO_Input_t, iname="_".join(str(field) for field in path))
            for path in ipath_to_type
        ]
        self.inputs = {
            path: inode.select(isel(t))
            for inode, (path, t) in zip(real_inputs, ipath_to_type.items())
        }
        self.outputs = {}
        self.run(dag)
        real_sources = [self.node_map[s] for s in dag.sources[1:]]
        real_sinks = [self.node_map[s] for s in dag.sinks[1:]]
        return IODag(
            inputs=real_inputs,
            outputs=self.outputs.values(),
            sources=real_sources,
            sinks=real_sinks,
        )

    def visit_Output(self, node: Output):
        Visitor.generic_visit(self, node)
        for field, child in zip(node.type.field_dict, node.children()):
            child_paths = self.node_to_opaths[child]
            for child_path, new_child in child_paths.items():
                new_path = (field, *child_path)
                assert new_path in self.opath_to_type
                child_t = self.opath_to_type[new_path]
                if child_t == Bit:
                    combine_children = [
                        Constant(type=BitVector[16], value=Unbound),
                        new_child,
                    ]
                else:
                    combine_children = [new_child, Constant(type=Bit, value=Unbound)]
                cnode = Combine(*combine_children, type=IO_Output_t)

                # Bad hack, read_en signals aren't actually connected to anything, this should be checked
                if "read_en" not in field:
                    self.outputs[new_path] = Output(
                        cnode,
                        type=IO_Output_t,
                        iname="_".join(str(field) for field in new_path),
                    )

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


def print_netlist_info(info, pes_with_packed_ponds, filename):
    outfile = open(filename, "w")
    print("pes with packed ponds", file=outfile)
    for k, v in pes_with_packed_ponds.items():
        print(f"  {k}  {v}", file=outfile)

    print("id to instance name", file=outfile)
    for k, v in info["id_to_name"].items():
        print(f"  {k}  {v}", file=outfile)

    print("id_to_Instrs", file=outfile)
    for k, v in info["id_to_instrs"].items():
        print(f"  {k}, {v}", file=outfile)

    print("id_to_metadata", file=outfile)
    for k, v in info["id_to_metadata"].items():
        print(f"  {k}, {v}", file=outfile)

    print("buses", file=outfile)
    for k, v in info["buses"].items():
        print(f"  {k}, {v}", file=outfile)

    print("netlist", file=outfile)
    for bid, v in info["netlist"].items():
        print(f"  {bid}", file=outfile)
        for _v in v:
            print(f"    {_v}", file=outfile)
    outfile.close()


def is_unbound_const(node):
    return isinstance(node, Constant) and node.value is Unbound


class VerifyUniqueIname(Visitor):
    def __init__(self):
        self.inames = {}

    def generic_visit(self, node):
        Visitor.generic_visit(self, node)
        if node.iname in self.inames:
            raise ValueError(
                f"{node.iname} for {node} already used by {self.inames[node.iname]}"
            )
        self.inames[node.iname] = node


class PipelineBroadcastHelper(Visitor):
    def __init__(self):
        self.sinks = {}

    def doit(self, dag: Dag):
        self.run(dag)
        for sink in dag.sinks:
            if hasattr(sink, "source"):
                self.sinks[sink] = [sink.source]
        return self.sinks

    def generic_visit(self, node: DagNode):
        for child in node.children():
            if child not in self.sinks:
                self.sinks[child] = []
            self.sinks[child].append(node)
        Visitor.generic_visit(self, node)


RegisterSource, RegisterSink = Common.create_dag_node(
    "Register",
    1,
    True,
    static_attrs=dict(input_t=BitVector[16], output_t=BitVector[16]),
)
BitRegisterSource, BitRegisterSink = Common.create_dag_node(
    "Register", 1, True, static_attrs=dict(input_t=Bit, output_t=Bit)
)


class FixInputsOutputAndPipeline(Visitor):
    def __init__(
        self,
        sinks,
        pipeline_inputs,
        harden_flush,
        max_flush_cycles,
        max_tree_leaves,
        tree_branch_factor,
    ):
        self.sinks = sinks

        self.pipeline_inputs = pipeline_inputs

        self.harden_flush = harden_flush
        self.max_flush_cycles = max_flush_cycles

        # Control IO broadcast pipelining tree creation
        self.max_tree_leaves = max_tree_leaves
        self.tree_branch_factor = tree_branch_factor

        self.max_sinks = 0
        for node, sink in sinks.items():
            self.max_sinks = max(self.max_sinks, len(sink))

        max_curr_tree_leaves = min(self.max_tree_leaves, self.max_sinks)
        self.num_stages = (
            math.ceil(math.log(max_curr_tree_leaves, self.tree_branch_factor)) + 1
        )

    def doit(self, dag: Dag):
        self.node_map = {}
        self.added_regs = 0
        self.inputs = []
        self.outputs = []
        self.dag_sources = dag.sources
        self.dag_sinks = dag.sinks
        self.run(dag)
        real_sources = [self.node_map[s] for s in self.dag_sources[1:]]
        real_sinks = [self.node_map[s] for s in self.dag_sinks[1:]]
        return IODag(
            inputs=self.inputs,
            outputs=self.outputs,
            sources=real_sources,
            sinks=real_sinks,
        )

    def create_register_tree(
        self,
        new_io_node,
        new_select_node,
        old_select_node,
        sinks,
        bit,
        min_stages=1,
    ):

        if bit:
            register_source = BitRegisterSource
            register_sink = BitRegisterSink
        else:
            register_source = RegisterSource
            register_sink = RegisterSink

        max_curr_tree_leaves = min(self.max_tree_leaves, len(sinks))
        num_stages = max(self.num_stages, min_stages)

        print(
            "Creating register tree for:",
            new_io_node.iname,
            "with",
            len(sinks),
            "sinks and",
            num_stages,
            "stages",
        )

        levels = [max_curr_tree_leaves]

        while 1 not in levels:
            levels.insert(0, math.ceil(levels[0] / self.tree_branch_factor))
        if num_stages > len(levels):
            for _ in range(num_stages - len(levels)):
                levels.insert(0, 1)

        sources = []

        new_reg_sink = register_sink(
            new_select_node, iname=new_io_node.iname + "$reg" + str(self.added_regs)
        )
        new_reg_source = register_source(
            iname=new_io_node.iname + "$reg" + str(self.added_regs)
        )

        self.added_regs += 1
        self.dag_sources.append(new_reg_source)
        self.dag_sinks.append(new_reg_sink)
        self.node_map[new_reg_source] = new_reg_source
        self.node_map[new_reg_sink] = new_reg_sink
        sources.append(new_reg_source)

        for level in levels[1:]:
            sources_idx = 0
            new_sources = []
            for idx in range(level):
                new_reg_sink = register_sink(
                    sources[sources_idx],
                    iname=new_io_node.iname + "$reg" + str(self.added_regs),
                )
                new_reg_source = register_source(
                    iname=new_io_node.iname + "$reg" + str(self.added_regs)
                )

                self.added_regs += 1
                self.dag_sources.append(new_reg_source)
                self.dag_sinks.append(new_reg_sink)
                self.node_map[new_reg_source] = new_reg_source
                self.node_map[new_reg_sink] = new_reg_sink
                new_sources.append(new_reg_source)
                if (idx + 1) % self.tree_branch_factor == 0:
                    sources_idx += 1
            sources = new_sources

        source_idx = 0
        nodes_per_leaf = math.floor((len(sinks)) / max_curr_tree_leaves)
        for idx, sink in enumerate(sinks):
            children_temp = list(sink.children())
            reg_index = children_temp.index(old_select_node)
            children_temp[reg_index] = sources[source_idx]
            if (idx + 1) % nodes_per_leaf == 0 and (source_idx + 1) < len(sources):
                source_idx += 1
            sink.set_children(*children_temp)

    def visit_Select(self, node: DagNode):
        Visitor.generic_visit(self, node)
        if not (
            "hw_output" in [child.iname for child in node.children()]
            or "self" in [child.iname for child in node.children()]
        ):
            new_children = [self.node_map[child] for child in node.children()]
            io_child = new_children[0]

            if "io16in" in io_child.iname:
                new_node = new_children[0].select("io2f_17")
                if self.pipeline_inputs:
                    self.create_register_tree(
                        io_child,
                        new_node,
                        node,
                        self.sinks[node],
                        False,
                        min_stages=self.max_flush_cycles,
                    )
            elif "io1in" in io_child.iname:
                new_node = new_children[0].select("io2f_1")
                if self.pipeline_inputs:
                    self.create_register_tree(
                        io_child,
                        new_node,
                        node,
                        self.sinks[node],
                        True,
                        min_stages=1,
                    )
            else:
                new_node = node.copy()

            if node not in self.node_map:
                new_node.set_children(*new_children)
                self.node_map[node] = new_node

    def generic_visit(self, node: DagNode):
        Visitor.generic_visit(self, node)
        if node.node_name == "global.IO" or node.node_name == "global.BitIO":
            if "write" in node.iname:
                new_node = Output(type=IO_Output_t, iname=node.iname)
                new_children = []

                for child in node.children():
                    if node.node_name == "global.IO":
                        new_reg_sink = RegisterSink(
                            self.node_map[child],
                            iname=node.iname + "$reg" + str(self.added_regs),
                        )
                        new_reg_source = RegisterSource(
                            iname=node.iname + "$reg" + str(self.added_regs)
                        )
                    else:
                        new_reg_sink = BitRegisterSink(
                            self.node_map[child],
                            iname=node.iname + "$reg" + str(self.added_regs),
                        )
                        new_reg_source = BitRegisterSource(
                            iname=node.iname + "$reg" + str(self.added_regs)
                        )
                    self.dag_sources.append(new_reg_source)
                    self.dag_sinks.append(new_reg_sink)
                    self.node_map[new_reg_source] = new_reg_source
                    self.node_map[new_reg_sink] = new_reg_sink
                    self.added_regs += 1
                    new_children.append(new_reg_source)

                new_node.set_children(*new_children)
                self.outputs.append(new_node)
            else:
                new_node = Input(type=IO_Input_t, iname=node.iname)
                self.inputs.append(new_node)

            self.node_map[node] = new_node
        else:
            if not (
                node.node_name == "Input"
                or "Input" in [child.node_name for child in node.children()]
            ):
                new_children = [self.node_map[child] for child in node.children()]
                new_node = node.copy()
                if node not in self.node_map:
                    new_node.set_children(*new_children)
                    self.node_map[node] = new_node


class PackRegsIntoPonds(Visitor):
    def __init__(self, sinks):
        self.sinks = sinks

    def doit(self, dag: Dag):
        self.skip_reg_nodes = []
        self.swap_pond_ports = set()
        self.pe_to_pond_conns = {}
        self.pond_reg_skipped = {}
        self.node_map = {}
        self.inputs = []
        self.outputs = []
        self.dag_sources = []
        self.dag_sinks = []
        self.run(dag)
        for source in dag.sources:
            if hasattr(source, "sink"):
                self.dag_sources.append(source)
                self.dag_sinks.append(source.sink)
        real_sources = [
            self.node_map[s] for s in self.dag_sources if s in self.node_map
        ]
        real_sinks = [self.node_map[s] for s in self.dag_sinks if s in self.node_map]
        return (
            IODag(
                inputs=self.inputs,
                outputs=self.outputs,
                sources=real_sources,
                sinks=real_sinks,
            ),
            self.pond_reg_skipped,
            self.swap_pond_ports
        )

    def find_pe(self, node, num_regs, reg_skip_list):
        if node.node_name == "global.PE":
            return node, num_regs, reg_skip_list

        assert node in self.sinks
        assert len(self.sinks[node]) == 1
        new_node = self.sinks[node][0]
        if new_node.node_name == "Register":
            reg_skip_list.append(new_node)
            if not isinstance(node, Sink):
                num_regs += 1
        return self.find_pe(new_node, num_regs, reg_skip_list)

    def generic_visit(self, node: DagNode):
        Visitor.generic_visit(self, node)
        if node in self.skip_reg_nodes:
            return

        n_node = node

        if (
            node.node_name == "Select"
            and node.child.node_name == "cgralib.Pond"
            and not isinstance(node.child, Sink)
            and node.field == "data_out_pond_0"
        ):
            pe_node, num_regs, reg_skip_list = self.find_pe(node, 0, [])
            if pe_node not in self.pe_to_pond_conns:
                self.pe_to_pond_conns[pe_node] = node
                self.pond_reg_skipped[node.child.iname] = num_regs
                self.skip_reg_nodes += reg_skip_list
            else:
                # Multiple ponds are connecting to one PE using the data_out_pond_0 port
                n_node = node.child.select("data_out_pond_1")
                self.swap_pond_ports.add(n_node.child.iname)

        if n_node in self.pe_to_pond_conns:
            new_children = []
            for child in n_node.children():
                if child in self.node_map:
                    new_children.append(self.node_map[child])
                else:
                    new_children.append(self.pe_to_pond_conns[n_node])
            new_node = n_node.copy()
            if n_node not in self.node_map:
                new_node.set_children(*new_children)
                self.node_map[n_node] = new_node
        else:
            new_children = [self.node_map[child] for child in n_node.children()]
            new_node = n_node.copy()
            new_node.set_children(*new_children)
            self.node_map[node] = new_node
            if n_node.node_name == "Output":
                self.outputs.append(new_node)
            if n_node.node_name == "Input":
                self.inputs.append(new_node)


class CountTiles(Visitor):
    def __init__(self):
        pass

    def doit(self, dag: Dag):
        self.num_pes = 0
        self.num_mems = 0
        self.num_ponds = 0
        self.num_ios = 0
        self.num_regs = 0
        self.run(dag)
        print(f"PEs: {self.num_pes}")
        print(f"MEMs: {int(self.num_mems/2)}")
        print(f"Ponds: {int(self.num_ponds/2)}")
        print(f"IOs: {self.num_ios}")
        print(f"Regs: {int(self.num_regs/2)}")

    def generic_visit(self, node: DagNode):
        Visitor.generic_visit(self, node)
        if node.node_name == "Input" or node.node_name == "Output":
            self.num_ios += 1
        elif node.node_name == "global.PE":
            self.num_pes += 1
        elif node.node_name == "cgralib.Mem":
            self.num_mems += 1
        elif node.node_name == "cgralib.Pond":
            self.num_ponds += 1
        elif node.node_name == "Register":
            self.num_regs += 1


def create_netlist_info(
    app_dir,
    dag: Dag,
    tile_info: dict,
    load_only=False,
    harden_flush=False,
    max_flush_cycles=0,
    pipeline_input_broadcasts=False,
    input_broadcast_branch_factor=4,
    input_broadcast_max_leaves=16,
):

    if load_only:
        id_to_name_filename = os.path.join(app_dir, f"design.id_to_name")
        if os.path.isfile(id_to_name_filename):
            fin = open(id_to_name_filename, "r")
            lines = fin.readlines()

            id_to_name = {}

            for line in lines:
                id_to_name[line.split(": ")[0]] = line.split(": ")[1].rstrip()

    sinks = PipelineBroadcastHelper().doit(dag)
    fdag = FixInputsOutputAndPipeline(
        sinks,
        pipeline_input_broadcasts,
        harden_flush,
        max_flush_cycles,
        input_broadcast_max_leaves,
        input_broadcast_branch_factor,
    ).doit(dag)

    sinks = PipelineBroadcastHelper().doit(fdag)
    pdag, pond_reg_skipped, swap_pond_ports = PackRegsIntoPonds(sinks).doit(fdag)

    def tile_to_char(t):
        if t.split(".")[1] == "PE":
            return "p"
        elif t.split(".")[1] == "Mem":
            return "m"
        elif t.split(".")[1] == "Pond":
            return "M"
        elif t.split(".")[1] == "IO":
            return "I"
        elif t.split(".")[1] == "BitIO":
            return "i"

    node_info = {t: tile_to_char(t) for t in tile_info}
    nodes_to_ids = CreateIDs(node_info).doit(pdag)

    if load_only:
        name_to_id = {name: id_ for id_, name in id_to_name.items()}

    info = {}
    info["id_to_name"] = {id: node for node, id in nodes_to_ids.items()}

    node_to_metadata = CreateMetaData().doit(pdag)
    info["id_to_metadata"] = {}
    for node, md in node_to_metadata.items():
        info["id_to_metadata"][nodes_to_ids[node]] = md
        if node in pond_reg_skipped:
            info["id_to_metadata"][nodes_to_ids[node]]["config"]["regfile2out_0"][
                "cycle_starting_addr"
            ][0] += pond_reg_skipped[node]
        elif node in swap_pond_ports:
            assert "regfile2out_1" not in info["id_to_metadata"][nodes_to_ids[node]]["config"]
            new_config = {}
            new_config["in2regfile_0"] = info["id_to_metadata"][nodes_to_ids[node]]["config"]["in2regfile_0"]
            new_config["regfile2out_1"] = info["id_to_metadata"][nodes_to_ids[node]]["config"]["regfile2out_0"]
            info["id_to_metadata"][nodes_to_ids[node]]["config"] = new_config

    nodes_to_instrs = CreateInstrs(node_info).doit(pdag)
    info["id_to_instrs"] = {
        id: nodes_to_instrs[node] for node, id in nodes_to_ids.items()
    }

    info["instance_to_instrs"] = {
        node: nodes_to_instrs[node]
        for node, id in nodes_to_ids.items()
        if ("p" in id or "m" in id or "I" in id or "i" in id)
    }
    for node, md in node_to_metadata.items():
        info["instance_to_instrs"][node] = md

    node_info = {t: fc.Py.input_t for t, fc in tile_info.items()}
    bus_info, netlist = CreateBuses(node_info).doit(pdag)
    info["buses"] = bus_info
    info["netlist"] = {}
    for bid, ports in netlist.items():
        info["netlist"][bid] = [
            (nodes_to_ids[node.iname], field) for node, field in ports
        ]

    if os.path.isfile(app_dir + "manual.place"):
        os.remove(app_dir + "manual.place")

    graph = NetlistGraph(info)
    # graph.generate_tile_id()
    graph.get_in_ub_latency(app_dir = app_dir)

    if "MANUAL_PLACER" in os.environ:
        # remove mem reg in conn for manual placement
        graph.remove_mem_reg_tree()

        # # generate tiles connection info
        # graph.generate_tile_conn()

        # manual placement
        graph.manualy_place_resnet(app_dir = app_dir)

    CountTiles().doit(pdag)

    return info
