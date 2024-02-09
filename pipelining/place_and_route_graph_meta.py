import sys
import os
import argparse
import re
import itertools
import glob
import json
 
from graphviz import Digraph

from pycyclone.io import load_placement
# parse raw routing result
from canal.pnr_io import __parse_raw_routing_result
from typing import Dict, List, Set
from .new_visualizer import visualize_pnr

class Node:

    def __init__(self, type_, x, y, tile_id = None, route_type = None, track = None, side = None, io = None, bit_width = None, port = None, net_id = None, reg_name = None, rmux_name = None, reg = False, kernel = None):
        assert x != None
        assert y != None
        if type_ == "tile":
            assert tile_id != None
            self.tile_id = tile_id 
        elif type_ == "route":
            assert bit_width != None
            self.tile_id = f"{type_ or 0},{route_type or 0},{x or 0},{y or 0},{track or 0},{side or 0},{io or 0},{bit_width or 0},{port or 0},{net_id or 0},{reg_name or 0},{rmux_name or 0},{reg}"

        self.type_ = type_
        self.route_type = route_type
        self.track = track 
        self.x = x 
        self.y = y 
        self.side = side 
        self.io = io 
        self.bit_width = bit_width 
        self.port = port 
        self.net_id = net_id
        self.reg_name = reg_name
        self.rmux_name = rmux_name
        self.reg = reg
        self.kernel = kernel
    
    def update_tile_id(self):
        if self.type_ == "tile":
            assert self.tile_id != None
            self.tile_id = self.tile_id 
        elif self.type_ == "route":
            assert self.bit_width != None
            self.tile_id = f"{self.type_ or 0},{self.route_type or 0},{self.x or 0},{self.y or 0},{self.track or 0},{self.side or 0},{self.io or 0},{self.bit_width or 0},{self.port or 0},{self.net_id or 0},{self.reg_name or 0},{self.rmux_name or 0},{self.reg}"

    def to_route(self):
        assert self.type_ == 'route'

        if self.route_type == "SB":
            route_string = f"{self.route_type} ({self.track}, {self.x}, {self.y}, {self.side}, {self.io}, {self.bit_width})"
        elif self.route_type == "PORT":
            route_string = f"{self.route_type} ({self.port}, {self.x}, {self.y}, {self.bit_width})"
        elif self.route_type == "REG":
            route_string = f"{self.route_type} ({self.reg_name}, {self.track}, {self.x}, {self.y}, {self.bit_width})"
        elif self.route_type == "RMUX":
            route_string = f"{self.route_type} ({self.rmux_name}, {self.x}, {self.y}, {self.bit_width})"
        else:
            raise ValueError("Unrecognized route type")
        return route_string

    def to_route(self):
        assert self.type_ == 'route'

        if self.route_type == "SB":
            route = [self.route_type, self.track, self.x, self.y, self.side, self.io, self.bit_width]
        elif self.route_type == "PORT":
            route = [self.route_type, self.port, self.x, self.y, self.bit_width]
        elif self.route_type == "REG":
            route = [self.route_type, self.reg_name, self.track, self.x, self.y, self.bit_width]
        elif self.route_type == "RMUX":
            route = [self.route_type, self.rmux_name, self.x, self.y, self.bit_width]
        else:
            raise ValueError("Unrecognized route type")
        return route

    def to_string(self):
        if self.type_ == "tile":
            return f"{self.tile_id} x:{self.x} y:{self.y} {self.kernel}"
        else:
            return f"{self.route_type} x:{self.x} y:{self.y}\nt:{self.track} bw:{self.bit_width} n:{self.net_id}\np:{self.port} r:{self.reg} {self.kernel}"

class Graph:
    def __init__(self):
        self.nodes: Dict[str, Node] = {}
        self.edges: List[(str, str)] = []
        self.inputs:List[str] = []
        self.outputs: List[str] = []
        self.sources: Dict[str, List[str]] = {}
        self.sinks: Dict[str, List[str]] = {}
        self.id_to_name: Dict[str, str] = {}
        self.added_regs = 0

    def get_node(self, node: str):
        if node in self.nodes:
            return self.nodes[node]
        return None

    def get_tiles(self):
        tiles = []
        for node in self.nodes:
            if self.get_node(node).type_ == "tile":
                tiles.append(node)
        return tiles

    def get_mems(self):
        mems = []
        for node in self.nodes:
            if self.get_node(node).type_ == "tile" and self.get_node(node).tile_id[0] == 'm':
                mems.append(node)
        return mems

    def get_pes(self):
        pes = []
        for node in self.nodes:
            if self.get_node(node).type_ == "tile" and self.get_node(node).tile_id[0] == 'p':
                pes.append(node)
        return pes

    def get_input_ios(self):
        ios = []
        for node in self.nodes:
            if self.get_node(node).type_ == "tile" and (self.get_node(node).tile_id[0] == 'I' or self.get_node(node).tile_id[0] == 'i') and len(self.sources[node]) == 0:
                ios.append(node)
        return ios

    def get_output_ios(self):
        ios = []
        for node in self.nodes:
            if self.get_node(node).type_ == "tile" and (self.get_node(node).tile_id[0] == 'I' or self.get_node(node).tile_id[0] == 'i') and len(self.sinks[node]) == 0:
                ios.append(node)
        return ios

    def is_reachable(self, source, dest):
        visited = set()
        queue = []

        queue.append(source)
        visited.add(source)

        while queue:
            n = queue.pop()

            if n == dest:
                return True

            for node in self.sinks[n]:
                if node not in visited:
                    queue.append(node)
                    visited.add(node)
        return False


    def add_node(self, node: Node):
        self.nodes[node.tile_id] = node

    def add_edge(self, node1, node2):
        if type(node1) == str:
            node1_name = node1
        elif type(node1) == Node:
            node1_name = node1.tile_id
        else:
            raise TypeError(f"Source node is type {type(node1)}")

        if type(node2) == str:
            node2_name = node2
        elif type(node2) == Node:
            node2_name = node2.tile_id
        else:
            raise TypeError(f"Dest node is type {type(node2)}")

        assert node1_name in self.nodes, f"{node1_name} not in nodes"
        assert node2_name in self.nodes, f"{node2_name} not in nodes"
        if (node1_name, node2_name) not in self.edges:
            self.edges.append((node1_name, node2_name))

    def update_sources_and_sinks(self):
        self.inputs = []
        self.outputs = []
        for node in self.nodes:
            self.sources[node] = []
            self.sinks[node] = []
        for node in self.nodes:
            for source,sink in self.edges:
                if node == source:
                    self.sources[sink].append(source)
                elif node == sink:
                    self.sinks[source].append(sink)
        for node in self.nodes:
            if len(self.sources[node]) == 0:
                self.inputs.append(node)
            if len(self.sinks[node]) == 0:
                self.outputs.append(node)

    def update_edge_kernels(self):
        for out_node in self.inputs:
            queue = []
            visited = set()
            kernel = self.get_node(out_node).kernel
            queue.append(out_node)
            visited.add(out_node)
            while queue:
                n = queue.pop()
                # if self.get_node(n).type_ == "tile":
                kernel = self.get_node(n).kernel

                for node in self.sinks[n]:
                    if node not in visited:
                        queue.append(node)
                        visited.add(node)
                        if self.get_node(node).type_ == "route":
                            self.get_node(node).kernel = kernel
        for tile in self.get_tiles():
            for source in self.sources[tile]:
                self.get_node(source).kernel = self.get_node(tile).kernel


    def print_graph(self, filename):
        g = Digraph()
        for node in self.nodes:
            g.node(node, label = self.get_node(node).to_string())

        for edge in self.edges:
            if self.get_node(edge[0]).net_id != None:
                net_id = self.get_node(edge[0]).net_id
            else:
                net_id = self.get_node(edge[1]).net_id

            g.edge(edge[0], edge[1], label=net_id)
            
        g.render(filename=filename)

    def print_graph_tiles_only(self, filename):
        g = Digraph()
        for source in self.get_tiles():
            if source[0] == 'r':
                g.node(source, label = f"{source}\n{self.get_node(source).kernel}", shape='box')
            else:
                g.node(source, label = f"{source}\n{self.get_node(source).kernel}")
            for dest in self.get_tiles():
                reachable = False
                visited = set()
                queue = []
                queue.append(source)
                visited.add(source)
                while queue:
                    n = queue.pop()

                    if n == dest and n != source:
                        reachable = True

                    for node in self.sinks[n]:
                        if node not in visited:
                            if self.get_node(node).type_ == "tile":
                                if node == dest:
                                    reachable = True
                            else:
                                queue.append(node)
                                visited.add(node)

                if reachable:
                    if self.get_node(source).net_id != None:
                        net_id = self.get_node(source).net_id
                    else:
                        net_id = self.get_node(dest).net_id
                    g.edge(source, dest, label=net_id)
            
        g.render(filename=filename)


    def topological_sort(self):
        visited = set()
        stack: List[str] = []
        for n in self.inputs:
            if n not in visited:
                self.topological_sort_helper(n, stack, visited)
        return stack[::-1]

    def topological_sort_helper(self, node: str, stack, visited: Set[str]):
        visited.add(node)
        for ns in self.sinks[node]:
            if ns not in visited:
                self.topological_sort_helper(ns, stack, visited)
        stack.append(node)


def parse_args():
    parser = argparse.ArgumentParser("CGRA Retiming tool")
    parser.add_argument("-a", "--app", "-d", required=True, dest="application", type=str, help="Application directory")
    parser.add_argument("-f", "--min-frequency", default=200, dest="frequency", type=int,
                        help="Minimum frequency in MHz")
    args = parser.parse_args()
    # check filenames
    # assert 1000 > args.frequency > 0, "Frequency must be less than 1GHz"
    dirname = os.path.join(args.application, "bin")
    netlist = os.path.join(dirname, "design.packed")
    assert os.path.exists(netlist), netlist + " does not exist"
    placement = os.path.join(dirname, "design.place")
    assert os.path.exists(placement), placement + " does not exists"
    route = os.path.join(dirname, "design.route")
    assert os.path.exists(route), route + " does not exists"
    # need to load routing files as well
    # for now we just assume RMUX exists
    return netlist, placement, route, args.frequency

def load_netlist(netlist_file):
    f = open(netlist_file, "r")
    lines = f.readlines()
 
    netlist = {}
    id_to_name = {}
    netlist_read = False
    id_to_name_read = False

    for line in lines:
        if "Netlists:" in line:
            netlist_read = True
        elif "ID to Names:" in line:
            netlist_read = False
            id_to_name_read = True
        elif "Netlist Bus:" in line:
            netlist_read = False
            id_to_name_read = False
        elif netlist_read:
            if len(line.split(":")) > 1:
                edge_id = line.split(":")[0]
                connections = line.split(":")[1]

                connections = re.findall(r'\b\S+\b', connections)

                netlist[edge_id] = []
                for conn1, conn2 in zip(connections[::2], connections[1::2]):
                    netlist[edge_id].append((conn1, conn2))
        elif id_to_name_read:
            if len(line.split(":")) > 1:
                id = line.split(":")[0]
                name = line.split(":")[1]
                id_to_name[id] = name.strip()
              
    return netlist, id_to_name

def load_folded_regs(folded_file):
    f = open(folded_file, "r")
    lines = f.readlines()
    pe_reg = set()
 
    for line in lines:
        reg_entry = re.findall(r'\b\S+\b', line.split(":")[0])
        entry = re.findall(r'\b\S+\b', line.split(":")[1])
        blk_id = entry[0]
        port = entry[-1]
        if reg_entry[0][0] == 'r' and blk_id[0] == 'p':
            pe_reg.add(((reg_entry[0], reg_entry[1]),(blk_id, port)))

    return pe_reg

def load_shift_regs(shift_regs_file, pe_reg):
    shift_regs = set()
    folded_regs = {reg:pe for (reg,_),pe in pe_reg}

    f = open(shift_regs_file, "r")
    lines = f.readlines()
    pe_reg = set()
 
    for line in lines:
        id = line.strip()
        shift_regs.add((id, None))
        if id in folded_regs:
            shift_regs.add(folded_regs[id])        
    return shift_regs

def segment_to_node(segment, net_id):
    if segment[0] == "SB":
        track, x, y, side, io_, bit_width = segment[1:]
        node1 = Node("route", x, y, route_type = "SB", track = track, side = side, io = io_, bit_width = bit_width, net_id = net_id)
    elif segment[0] == "PORT":
        port_name, x, y, bit_width = segment[1:]
        node1 = Node("route", x, y, route_type = "PORT", bit_width = bit_width, net_id = net_id, port = port_name)
    elif segment[0] == "REG":
        reg_name, track, x, y, bit_width = segment[1:]
        node1 = Node("route", x, y, route_type = "REG", track = track, bit_width = bit_width, net_id = net_id, reg_name = reg_name)
    elif segment[0] == "RMUX":
        rmux_name, x, y, bit_width = segment[1:]
        node1 = Node("route", x, y, route_type = "RMUX", bit_width = bit_width, net_id = net_id, rmux_name = rmux_name)
    else:
        raise ValueError("Unrecognized route type")
    return node1

def get_tile_at(x, y, bw, placement, reg = False):
    for tile_id, place in placement.items():
        if (x,y) == place:
            if reg:
                if tile_id[0] == 'r':
                    return tile_id
            else:
                if tile_id[0] == "I" and bw == 16:
                    return tile_id
                elif tile_id[0] == "i" and bw == 1:
                    return tile_id
                elif tile_id[0] != "I" and tile_id[0] != "i":
                    return tile_id
    return None


def construct_graph(placement, routes, id_to_name):
    graph = Graph()
    graph.id_to_name = id_to_name
    max_reg_id = 0

    for blk_id, place in placement.items():
        if len(graph.id_to_name[blk_id].split("$")) > 0:
            kernel = graph.id_to_name[blk_id].split("$")[0]
        else:
            kernel = None
        node = Node("tile", place[0], place[1], tile_id=blk_id, kernel = kernel)
        graph.add_node(node)
        max_reg_id = max(max_reg_id, int(blk_id[1:]))
    graph.added_regs = max_reg_id + 1

    for net_id, net in routes.items():
        for route in net:
            for seg1, seg2 in zip(route, route[1:]):
                node1 = segment_to_node(seg1, net_id)
                graph.add_node(node1)
                node2 = segment_to_node(seg2, net_id)
                graph.add_node(node2)
                graph.add_edge(node1, node2)
                
                if node1.route_type == "PORT":
                    tile_id = get_tile_at(node1.x, node1.y, node1.bit_width, placement)
                    if tile_id[0] == "m" and node1.port != "flush":
                        node1.reg = True
                    graph.add_edge(tile_id, node1)
                elif node1.route_type == "REG":
                    tile_id = get_tile_at(node1.x, node1.y, node1.bit_width, placement, reg = True)
                    graph.add_edge(tile_id, node1)

                if node2.route_type == "PORT":
                    tile_id = get_tile_at(node2.x, node2.y, node2.bit_width, placement)
                    # if tile_id[0] == "m" and node2.port != "flush":
                    #     node2.reg = True
                    graph.add_edge(node2, tile_id)
                elif node2.route_type == "REG":
                    node2.reg = True
                    tile_id = get_tile_at(node2.x, node2.y, node2.bit_width, placement, reg = True)
                    graph.add_edge(node2, tile_id)

    graph.update_sources_and_sinks()
    graph.update_edge_kernels()

    for pe in graph.get_pes():
        sources = graph.sources[pe]
        for source in sources:
            # if graph.get_node(source).port == port:
            graph.get_node(source).reg = True

    return graph

def verify_graph(graph):
    for node in graph.nodes:
        if len(graph.sources[node]) == 9:
            assert node in graph.inputs
            assert graph.get_node(node).type_ == "tile", f"{node} is a route"
            assert graph.get_node(node).tile_id[0] == "I" or graph.get_node(node).tile_id[0] == "i" or graph.get_node(node).tile_id[0] == "p"
        if len(graph.sinks[node]) == 0:
            assert node in graph.outputs
            assert graph.get_node(node).type_ == "tile", f"{node} is a route"
            assert graph.get_node(node).tile_id[0] == "I" or graph.get_node(node).tile_id[0] == "i"
    
PE_DELAY = 600
MEM_DELAY = 0
PE_SB = 140
MEM_SB = 140
RMUX_DELAY = 0
GLB_DELAY = 1100

class PathComponents:
    def __init__(self, glbs = 0, hops = 0, pes = 0, mems = 0, used_regs = 0, available_regs = 0, parent = None):
        self.glbs = glbs
        self.hops = hops
        self.pes = pes
        self.mems = mems
        self.available_regs = available_regs
        self.parent = parent

    def get_total(self):
        total = 0
        total += self.glbs * GLB_DELAY
        total += self.hops * PE_SB
        total += self.pes * PE_DELAY
        total += self.mems * MEM_DELAY
        return total

def sta(graph):
    nodes = graph.topological_sort()
    timing_info = {}

    for node in nodes:
        
        comp = PathComponents()
        components = [comp]

        if len(graph.sources[node]) == 0:
            comp = PathComponents()
            comp.glbs = 1
            components.append(comp)

        for parent in graph.sources[node]:

            comp = PathComponents()

            if parent in timing_info:
                comp.glbs = timing_info[parent].glbs
                comp.hops = timing_info[parent].hops
                comp.pes = timing_info[parent].pes
                comp.mems = timing_info[parent].mems
                comp.available_regs = timing_info[parent].available_regs
                comp.parent = parent
            
            g_node = graph.get_node(node)
            if g_node.type_ == "tile":
                if node[0] == 'p':
                    comp.pes += 1
                elif node[0] == 'm':
                    comp.mems += 1
                elif node[0] == 'I' or node[0] == 'i':
                    comp.glbs += 1
            else:
                if g_node.route_type == "SB":
                    if g_node.io == 1:
                        comp.hops += 1
                elif g_node.route_type == "RMUX":
                    if graph.get_node(parent).route_type != "REG":
                        comp.available_regs += 1
                if g_node.reg:
                    comp.glbs = 0
                    comp.hops = 0
                    comp.pes = 0
                    comp.mems = 0
                    comp.available_regs = 0
                    comp.parent = None
            components.append(comp)
        
        maxt = 0
        max_comp = components[0]
        for comp in components:
            if comp.get_total() > maxt:
                maxt = comp.get_total()
                max_comp = comp

        timing_info[node] = max_comp


    node_to_timing = {node:timing_info[node].get_total() for node in graph.nodes}
    node_to_timing = dict(sorted(node_to_timing.items(), key=lambda item: item[1], reverse=True))
    max_node = list(node_to_timing.keys())[0]
    max_delay = list(node_to_timing.values())[0]


    clock_speed = 1.0e12 / max_delay / 1e6

    print("Critical Path Info:")

    print("\tMaximum clock frequency:", clock_speed, "MHz")
    print("\tCritical Path:", max_delay, "ns")

    net_ids = set()

    curr_node = max_node
    net_ids.add(graph.get_node(curr_node).net_id)
    print("\t",curr_node, timing_info[curr_node].get_total(), "glb:", timing_info[curr_node].glbs, "hops:",  timing_info[curr_node].hops, "pes:", timing_info[curr_node].pes, "mems:", timing_info[curr_node].mems, "regs:", timing_info[curr_node].available_regs)
    crit_path = []
    crit_path.append((curr_node, timing_info[curr_node].get_total()))

    while(True):
        curr_node = timing_info[curr_node].parent
        if curr_node == None:
            break
        net_ids.add(graph.get_node(curr_node).net_id)
        crit_path.append((curr_node, timing_info[curr_node].get_total()))
        # print(curr_node, timing_info[curr_node].get_total(), "glb:", timing_info[curr_node].glbs, "hops:",  timing_info[curr_node].hops, "pes:", timing_info[curr_node].pes, "mems:", timing_info[curr_node].mems, timing_info[curr_node].available_regs)

    crit_path.reverse()

    print("\tCritical Path Nets:", *net_ids, "\n")
    
    # for idx, curr_node in enumerate(node_to_timing):
    #     if graph.get_node(curr_node).type_ == "route":
    #         continue
    #     if idx > 500:
    #         break
    #     print(curr_node, timing_info[curr_node].get_total(), timing_info[curr_node].glbs, timing_info[curr_node].hops, timing_info[curr_node].pes, timing_info[curr_node].mems, timing_info[curr_node].available_regs)
    return clock_speed, crit_path, net_ids

def find_break_idx(graph, crit_path):
    crit_path_adjusted = [abs(c - crit_path[0][1]/2) for n,c in crit_path]
    break_idx = crit_path_adjusted.index(min(crit_path_adjusted))
    while True:
        if graph.get_node(crit_path[break_idx + 1][0]).route_type == "RMUX" and graph.get_node(crit_path[break_idx][0]).route_type == "SB":
            return break_idx
        break_idx += 1

        if break_idx >= len(crit_path):
            break_idx = crit_path_adjusted.index(min(crit_path_adjusted))

            while True:
                if graph.get_node(crit_path[break_idx + 1][0]).route_type == "RMUX" and graph.get_node(crit_path[break_idx][0]).route_type == "SB":
                    return break_idx
                break_idx -= 1

                if break_idx < 1:
                    raise ValueError("Can't find available register on critical path")

def reg_into_route(routes, g_break_node_source, new_reg_route_source):
    for net_id, net in routes.items():
        for route in net:
            for idx, segment in enumerate(route):
                if g_break_node_source.to_route() == segment:
                    route.insert(idx + 1, new_reg_route_source.to_route())
                    return 

def break_crit_path(graph, id_to_name, crit_path, placement, routes):
    
    break_idx = find_break_idx(graph, crit_path)

    break_node_source = crit_path[break_idx][0]
    break_node_dest = graph.sinks[break_node_source][0]
    g_break_node_source = graph.get_node(break_node_source)
    g_break_node_dest = graph.get_node(break_node_dest)

    assert g_break_node_source.type_ == "route" 
    assert g_break_node_source.route_type == "SB" 
    assert g_break_node_dest.type_ == "route" 
    assert g_break_node_dest.route_type == "RMUX"

    x = g_break_node_source.x
    y = g_break_node_source.y
    track = g_break_node_source.track
    bw = g_break_node_source.bit_width
    net_id = g_break_node_source.net_id
    kernel = g_break_node_source.kernel
    side = g_break_node_source.side
    print("Breaking net:", net_id, "Kernel:", kernel, "\n")
    
    dir_map = {0: "EAST", 1: "SOUTH", 2: "WEST", 3: "NORTH"}

    new_segment = ["REG", f"T{track}_{dir_map[side]}", track, x, y, bw]
    new_reg_route_source = segment_to_node(new_segment, net_id)
    new_reg_route_source.reg = True
    new_reg_route_source.update_tile_id()
    new_reg_route_dest = segment_to_node(new_segment, net_id)
    new_reg_tile = Node("tile", x, y, tile_id=f"r{graph.added_regs}", kernel = kernel)
    graph.added_regs += 1
    
    graph.edges.remove((break_node_source, break_node_dest))

    graph.add_node(new_reg_route_source)
    graph.add_node(new_reg_tile)
    graph.add_node(new_reg_route_dest)

    graph.add_edge(break_node_source, new_reg_route_source)
    graph.add_edge(new_reg_route_source, new_reg_tile)
    graph.add_edge(new_reg_tile, new_reg_route_dest)
    graph.add_edge(new_reg_route_dest, break_node_dest)

    reg_into_route(routes, g_break_node_source, new_reg_route_source)
    placement[new_reg_tile.tile_id] = (new_reg_tile.x, new_reg_tile.y)
    id_to_name[new_reg_tile.tile_id] = f"pnr_pipelining{graph.added_regs}"

    graph.update_sources_and_sinks()
    graph.update_edge_kernels()


def compute_unit_cycles(graph):
    nodes = graph.topological_sort()
    node_cycles = {}


    for node in nodes:
        cycles = set()
        g_node = graph.get_node(node)

        if g_node.kernel not in node_cycles:
            node_cycles[g_node.kernel] = {}


        for parent in graph.sources[node]:
            g_parent = graph.get_node(parent)
            if parent not in node_cycles[g_node.kernel]:
                c = 0
            else:
                c = node_cycles[g_node.kernel][parent]
            
            if g_node.type_ == "route":
                if g_node.reg:
                    if parent not in graph.get_mems():
                        if c != None: 
                            c += 1
            if parent not in graph.get_mems():
                cycles.add(c)
        
  
        if node in graph.get_pes() and len(graph.sources[node]) == 0:
            cycles = {None}
  
        if None in cycles:
            cycles.remove(None)
        if len(graph.sources[node]) > 1 and len(cycles) > 1:
            print(f"INCORRECT COMPUTE UNIT CYCLES: {node} {cycles}")
        if len(cycles) > 0:
            node_cycles[g_node.kernel][node] = max(cycles)
        else:
            node_cycles[g_node.kernel][node] = None

    print("Kernel cycles:")

    kernel_latencies = {}

    for kernel in node_cycles:
        kernel_cycles = [cyc for cyc in node_cycles[kernel].values() if cyc != None]
        kernel_cycles.append(0)
        print("\t", kernel,  max(kernel_cycles))
        kernel_latencies[kernel] = max(kernel_cycles)

    print("\n")
    return kernel_latencies


def flush_cycles(graph):
    nodes = graph.topological_sort()
    node_cycles = {}
    kernel_latencies = {}

    for io in graph.get_input_ios():
        if graph.get_node(io).kernel == "flush":
            break

    flush_cycles = {}
    print("Flush cycles:")

    for mem in graph.get_mems():
        flush_cycles[mem] = 0
        for curr_node in graph.sources[mem]:
            if graph.get_node(curr_node).port == "flush":
                break
        while curr_node != io:
            g_curr_node = graph.get_node(curr_node)
            if g_curr_node.type_ == "route" and g_curr_node.reg:
                flush_cycles[mem] += 1

            assert len(graph.sources[curr_node]) == 1
            curr_node = graph.sources[curr_node][0]

        print("\t", mem, flush_cycles[mem])
        kernel_latencies[graph.get_node(mem).kernel] = flush_cycles[mem]

    print("\n")
    return kernel_latencies

def update_kernel_latencies(dir_name, graph):

    kernel_latencies_file = glob.glob(f"{dir_name}/*_compute_kernel_latencies.json")[0]

    assert os.path.exists(kernel_latencies_file)

    f = open(kernel_latencies_file, "r")
    kernel_latencies = json.load(f)

    new_latencies = compute_unit_cycles(graph)
    flush_latencies = flush_cycles(graph)

    # Unfortunately exact matches between kernels and memories dont exist, so we have to look them up
    sorted_new_latencies = {}
    for k in sorted(new_latencies, key=len):
        sorted_new_latencies[k] = new_latencies[k]

    sorted_flush_latencies = {}
    for k in sorted(flush_latencies, key=len):
        sorted_flush_latencies[k] = flush_latencies[k]

    used_kernels = set()
    used_lkernels = set()

    for kernel, lat in kernel_latencies.items():
        print(kernel)
        new_lat = lat

        if f"op_{kernel}" in sorted_new_latencies:
            new_lat = sorted_new_latencies[f"op_{kernel}"]
            used_kernels.add(f"op_{kernel}")
            print("found exact new latency", f"op_{kernel}")
        # else:
        #     for f_kernel, lat in sorted_new_latencies.items():
        #         if kernel in f_kernel:
        #             used_kernels.add(f_kernel)
        #             new_lat = sorted_new_latencies[f_kernel]
        #             print("found new latency", f_kernel)
        #             break


        f_kernel = kernel.split("hcompute_")[1]
        if f_kernel in sorted_flush_latencies:
            new_lat += sorted_flush_latencies[f_kernel]
            used_kernels.add(f_kernel)
            print("found exact flush latency", f_kernel)
        # for f_kernel, lat in sorted_flush_latencies.items():
        #     if f_kernel in kernel:
        #         used_lkernels.add(f_kernel)
        #         new_lat += sorted_flush_latencies[f_kernel]
        #         print("found flush", f_kernel)
        #         break
           
        kernel_latencies[kernel] = new_lat
        print("\n")

    fout = open(kernel_latencies_file, "w")
    fout.write(json.dumps(kernel_latencies))

def segment_node_to_string(node):
    if node[0] == "SB":
        return f"{node[0]} ({node[1]}, {node[2]}, {node[3]}, {node[4]}, {node[5]}, {node[6]})"
    elif node[0] == "PORT":
        return f"{node[0]} {node[1]} ({node[2]}, {node[3]}, {node[4]})"
    elif node[0] == "REG":
        return f"{node[0]} {node[1]} ({node[2]}, {node[3]}, {node[4]}, {node[5]})"
    elif node[0] == "RMUX":
        return f"{node[0]} {node[1]} ({node[2]}, {node[3]}, {node[4]})"

def dump_routing_result(dir_name, routing):

    route_name = os.path.join(dir_name, "design.route")

    fout = open(route_name, "w")

    for net_id, route in routing.items():
        fout.write(f"Net ID: {net_id} Segment Size: {len(route)}\n")
        src = route[0]
        for seg_index, segment in enumerate(route):
            fout.write(f"Segment: {seg_index} Size: {len(segment)}\n")

            for node in segment:
                fout.write(f"{segment_node_to_string(node)}\n")
        fout.write("\n")


def dump_placement_result(dir_name, placement, id_to_name):

    place_name = os.path.join(dir_name, "design.place")
    fout = open(place_name, "w")
    fout.write("Block Name			X	Y		#Block ID\n")
    fout.write("---------------------------\n")

    for tile_id, place in placement.items():
        fout.write(f"{id_to_name[tile_id]}\t\t{place[0]}\t{place[1]}\t\t#{tile_id}\n")
    fout.write("\n")


def pipeline_pnr(app_dir, placement, routing, id_to_name, target_freq):
    print("Generating graph of pnr result")
    graph = construct_graph(placement, routing, id_to_name)

    verify_graph(graph)
    # compute_unit_cycles(graph)

    curr_freq, crit_path, crit_nets = sta(graph)
    while curr_freq <= target_freq:
        break_crit_path(graph, id_to_name, crit_path, placement, routing)
        curr_freq, crit_path, crit_nets = sta(graph)

    update_kernel_latencies(app_dir, graph)

    if False:
        print("Printing graph of pnr result")
        graph.print_graph("pnr_graph")
        graph.print_graph_tiles_only("pnr_graph_tile")

    visualize_pnr(graph, crit_nets)
    return placement, routing, id_to_name

def main():
    netlist_file, placement_file, routing_file, target_freq = parse_args()

    print("Loading netlist")
    netlist, id_to_name = load_netlist(netlist_file)
    print("Loading placement")
    placement = load_placement(placement_file)
    print("Loading routing")
    routing = __parse_raw_routing_result(routing_file)

    app_dir = os.path.join(os.path.dirname(netlist_file), "design_top.json")

    pipeline_pnr(app_dir, placement, routing, id_to_name, target_freq)
    dump_routing_result(app_dir, routing)
    dump_placement_result(app_dir, placement, id_to_name)
    # route_stats(placement, route, timing_info)

    
if __name__ == "__main__":
    sys.path.append(os.path.dirname(os.path.realpath(__file__)))
    main()
