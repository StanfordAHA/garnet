import sys
import os

from .netlist_util import parse_and_pack_netlist, port_rename

from pycyclone.io import load_placement
# parse raw routing result
from canal.pnr_io import __parse_raw_routing_result
from typing import Dict, List, Tuple, Set

PE_DELAY = 1100
MEM_DELAY = 0
PE_SB = 210
MEM_SB = 300
RMUX_DELAY = 18
GLB_DELAY = 1300


class Node:
    def __init__(self, blk_id: str):
        self.next: Dict[str, List[Tuple["Node",str]]] = {}
        self.parent: Dict[str, Node] = {}
        self.blk_id = blk_id

    def add_next(self, src_port: str, sink_port, node: "Node"):
        if src_port not in self.next:
            self.next[src_port] = []
        self.next[src_port].append((node, sink_port))
        node.parent[sink_port] = self

    def __repr__(self):
        return self.blk_id


class Graph:
    def __init__(self):
        self.nodes: Dict[str, Node] = {}

    def get_node(self, blk_id: str):
        if blk_id not in self.nodes:
            node = Node(blk_id)
            self.nodes[blk_id] = node
        return self.nodes[blk_id]

    def sort(self):
        visited = set()
        stack: List[Node] = []

        for n in self.nodes.values():
            if n.blk_id not in visited:
                self.__sort(n, stack, visited)
        return stack[::-1]

    @staticmethod
    def __sort(node: Node, stack, visited: Set[str]):
        visited.add(node.blk_id)
        for ns in node.next.values():
            for n, _ in ns:
                Graph.__sort(n, stack, visited)
        stack.append(node)


def construct_graph(netlist):
    g = Graph()
    for net in netlist.values():
        src_id, src_port = net[0]
        src_node = g.get_node(src_id)
        for sink_id, sink_port in net[1:]:
            sink_node = g.get_node(sink_id)
            src_node.add_next(src_port, sink_port, sink_node)
    return g


def get_net_id(sink_pin, netlist):
    for net_id, net in netlist.items():
        if sink_pin == net[0]:
            return net_id
    return None


def compute_delay(net, routing, placement):
    node_timing = {}
    sink_pin_timing = {}
    for segment in routing:
        segment = [tuple(e) for e in segment]
        if segment[0] not in node_timing:
            node_timing[segment[0]] = 0
        t = node_timing[segment[0]]
        for node_str in segment[1:]:
            if node_str[0] == "SB":
                # we only count output of the SB
                track, x, y, side, io_, bit_width = node_str[1:]
                if io_ == 1:
                    # PE or MEM
                    if x % 4 == 3:
                        t += MEM_SB
                    else:
                        t += PE_SB
            elif node_str[0] == "RMUX":
                t += RMUX_DELAY
        # the end of the segment is the sink pinprint(segment[0])
        node_str = segment[-1]
        # it's either a register or a port
        if node_str[0] == "PORT":
            port_name, x, y, bit_width = node_str[1:]
            sink_pin_timing[(port_name, x, y)] = t
        else:
            assert node_str[0] == "REG"
            reg_name, track, x, y, bit_width = node_str[1:]
            # we use "reg" here
            sink_pin_timing[("reg", x, y)] = t
    # compute the actual pin delay using net and placement
    result = {}
    for blk_id, port in net[1:]:
        x, y = placement[blk_id]
        t = sink_pin_timing[(port, x, y)]
        result[(blk_id, port)] = t
    return result


def get_sink_nets(netlist, blk_id):
    result = {}
    for net_id, net in netlist.items():
        if net[0][0] == blk_id:
            result[net_id] = net
    return result


def main():
    if len(sys.argv) != 4:
        print("Usage: python -m mini_mapper.timing netlist.json design.place design.route", file=sys.stderr)
        exit(1)
    netlist_file = sys.argv[1]
    placement_file = sys.argv[2]
    routing_file = sys.argv[3]

    netlist, folded_blocks, id_to_name, changed_pe = \
        parse_and_pack_netlist(netlist_file, fold_reg=True)

    netlist = port_rename(netlist)

    # any block that folds to the PE needs to be 0
    pe_reg = set()
    for entry in folded_blocks.values():
        blk_id = entry[0]
        port = entry[-1]
        if blk_id[0] == 'p':
            pe_reg.add((blk_id, port))

    # parse the placement result
    placement = load_placement(placement_file)
    route = __parse_raw_routing_result(routing_file)

    # need to parse the route
    # we need to do simple STA analysis
    graph = construct_graph(netlist)
    nodes = graph.sort()
    timing = {}
    for node in nodes:
        blk_id = node.blk_id
        if blk_id[0] == 'r':
            output_ports = node.next.keys()
            for p in output_ports:
                timing[(blk_id, p)] = 0
            start_time = 0
        else:
            # the max delay to this point
            ts = [0]
            for src_port, parent in node.parent.items():
                if (blk_id, src_port) in pe_reg:
                    t = 0
                else:
                    if (parent.blk_id, src_port) not in timing:
                        timing[(parent.blk_id, src_port)] = 0
                    t = timing[(parent.blk_id, src_port)]
                ts.append(t)
            start_time = max(ts)
        # use the routing information to update each ports
        # need to add the operation delay
        if blk_id[0] == 'p':
            start_time += PE_DELAY
        elif blk_id[0] == 'm':
            start_time += MEM_DELAY
        nets = get_sink_nets(netlist, blk_id)
        for net_id, net in nets.items():
            delays = compute_delay(net, route[net_id], placement)
            for entry, t in delays.items():
                timing[entry] = start_time + t

    max_delay = max(timing.values()) + 2 * GLB_DELAY
    clock_speed = 1.0e12 / max_delay / 1e6
    print("Maximum clock frequency:", clock_speed, "MHz")


if __name__ == "__main__":
    sys.path.append(os.path.dirname(os.path.realpath(__file__)))
    main()
