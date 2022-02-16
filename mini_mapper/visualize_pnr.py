import random
import sys
from PIL import Image, ImageDraw
from archipelago.io import load_routing_result
from pycyclone.io import load_placement
import math
import os
import re
import argparse
from typing import Dict, List, Tuple, Set


def parse_args():
    parser = argparse.ArgumentParser("PnR Visualization tool")
    parser.add_argument("-a", "--app", "-d", required=True, dest="application", type=str, help="Application directory")
    parser.add_argument("--width", required=True, dest="width", type=str, help="CGRA width")
    parser.add_argument("--height", required=True, dest="height", type=str, help="CGRA height")
    parser.add_argument("--crit_net", required=False, dest="crit_net", nargs='*', type=str, help="Critical Net")
   
    args = parser.parse_args()
    # check filenames
    dirname = os.path.join(args.application, "bin")
    placement = os.path.join(dirname, "design.place")
    assert os.path.exists(placement), placement + " does not exists"
    route = os.path.join(dirname, "design.route")
    assert os.path.exists(route), route + " does not exists"
    folded = os.path.join(dirname, "design.folded")
    assert os.path.exists(folded), folded + " does not exists"
    # need to load routing files as well
    # for now we just assume RMUX exists
    return placement, route, folded, int(args.height) + 1, int(args.width) + 1, args.crit_net

def load_folded_regs(folded_file):
    f = open(folded_file, "r")
    lines = f.readlines()
    pe_reg = set()
 
    for line in lines:
        entry = re.findall(r'\b\S+\b', line.split(":")[1])
        blk_id = entry[0]
        port = entry[-1]
        if blk_id[0] == 'p':
            pe_reg.add((blk_id, port))

    return pe_reg

def arrowedLine(draw, ptA, ptB, size = 3, color=(0,255,0)):
    """Draw line from ptA to ptB with arrowhead at ptB"""
    # Get drawing context
    width=1

    # Draw the line without arrows
    draw.line((ptA,ptB), width=width, fill=color)
    

    # Now work out the arrowhead
    # = it will be a triangle with one vertex at ptB
    # - it will start at 95% of the length of the line
    # - it will extend 8 pixels either side of the line
    x0, y0 = ptA
    x1, y1 = ptB
    # Now we can work out the x,y coordinates of the bottom of the arrowhead triangle
    xb = 0*(x1-x0)+x0
    yb = 0*(y1-y0)+y0

    # Work out the other two vertices of the triangle
    # Check if line is vertical
    if x0==x1:
       vtx0 = (xb-size, yb)
       vtx1 = (xb+size, yb)
    # Check if line is horizontal
    elif y0==y1:
       vtx0 = (xb, yb+size)
       vtx1 = (xb, yb-size)
    else:
       alpha = math.atan2(y1-y0,x1-x0)-90*math.pi/180
       a = 8*math.cos(alpha)
       b = 8*math.sin(alpha)
       vtx0 = (xb+a, yb+b)
       vtx1 = (xb-a, yb-b)

    #draw.point((xb,yb), fill=(255,0,0))    # DEBUG: draw point of base in red - comment out draw.polygon() below if using this line
    #im.save('DEBUG-base.png')              # DEBUG: save

    # Now draw the arrowhead triangle
    draw.polygon([vtx0, vtx1, ptB], fill=color)


class Node:
    def __init__(self, blk_id: str):
        self.next: Dict[str, List[Tuple["Node", str]]] = {}
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


class Visualizer():
    def __init__(self, img_width, img_height, width, height, scale, num_tracks, raw_routing_result, raw_placement_result, port_map, color_index, color_palette, pe_reg):
        self.img_width = img_width 
        self.img_height = img_height 
        self.width = width 
        self.height = height 
        self.scale = scale
        self.num_tracks = num_tracks
        self.raw_routing_result = raw_routing_result
        self.raw_placement_result = raw_placement_result
        self.port_map = port_map
        self.color_index = color_index
        self.color_palette = color_palette
        self.pe_reg = pe_reg

    def parse_raw_routing_result(self):
        routes_list = []
        for edge_id, routes in self.raw_routing_result.items():

            route = {}
            route["edge_id"] = edge_id
            segment_list = []
            route["segments"] = segment_list
            track1 = None
            route["end_list"] = []
            for segments in routes:
                # print(segments[0])
                if segments[0][1] in self.port_map:
                    route["start"] = self.port_map[segments[0][1]]
                elif segments[0][0] != "SB":
                    route["start"] = "PE"

                if segments[-1][1] in self.port_map:
                    route["end"] = self.port_map[segments[-1][1]]
                elif segments[-1][0] != "SB":
                    route["end"] = "PE"


                for seg1 in segments:
                    if seg1[0] == "SB":
                        track1, x1, y1, side, io_, bit_width = seg1[1:]
                    elif seg1[0] == "PORT":
                        port_name, x1, y1, bit_width = seg1[1:]
                    elif seg1[0] == "REG":
                        reg_name, track1, x1, y1, bit_width = seg1[1:]
                    elif seg1[0] == "RMUX":
                        rmux_name, x1, y1, bit_width = seg1[1:]

                    if seg1 == segments[0]:
                        route["start_point"] = (x1, y1)
                    if seg1 == segments[-1]:
                        route["end_list"].append((x1, y1))
                    
                    route["bit_width"] = bit_width
                    
                    if len(route["segments"]) > 0:
                        last_x = route["segments"][-1]['x']
                        last_y = route["segments"][-1]['y']

                        if not (last_x == x1 and last_y == y1):
                            # if track1 == None:
                            #     breakpoint()
                            #     track1 = last_track
                            segment = {}
                            segment['x'] = x1
                            segment['y'] = y1
                            segment['track'] = track1
                            route["segments"].append(segment)
                    else:
                        segment = {}
                        segment['x'] = x1
                        segment['y'] = y1
                        segment['track'] = track1
                        route["segments"].append(segment)

                if route["segments"][0]['track'] == None:
                    route["segments"][0]['track'] = route["segments"][1]['track']
            routes_list.append(route)

        self.routes_list = routes_list
        self.unordered_routes = routes_list.copy()


    def sort_routes(self):
        ordered_routes = []
        ordered_routes.append([])
        visited_points = []

        for route in self.routes_list.copy():
            if route["start"] == "IO16":
                ordered_routes[0].append(route)
                self.routes_list.remove(route)
                for end_pts in route["end_list"]:
                    visited_points.append(end_pts)

        routes_idx = 1
        routes_list_len = len(self.routes_list)
        while True:
            ordered_routes.append([])
            visited_points_new = []
            for route in self.routes_list.copy():
                if route["start_point"] in visited_points:
                    ordered_routes[routes_idx].append(route)
                    self.routes_list.remove(route)
                    
                    for end_pts in route["end_list"]:
                        visited_points_new.append(end_pts)
                    
            
            if len(self.routes_list) == routes_list_len:
                for route in self.routes_list.copy():
                    ordered_routes[routes_idx].append(route)
                break
            routes_idx += 1
            visited_points += visited_points_new
            routes_list_len = len(self.routes_list)
        self.ordered_routes = ordered_routes
        self.visited_points = visited_points
    

    def sort_segments(self):
        for net_id, segments in self.raw_routing_result.items():
            segments_len = len(segments)
            if segments_len > 1:
                wont_sort = False
                segments_unsorted = []
                segments_dict = {}
                for segment in segments:
                    start = segment[0]
                    end = segment[-1]
                    if start[0] == "SB":
                        track1, start_x, start_y, side, io_, bit_width = start[1:]
                    elif start[0] == "PORT":
                        port_name, start_x, start_y, bit_width = start[1:]
                    elif start[0] == "REG":
                        reg_name, track1, start_x, start_y, bit_width = start[1:]
                    elif start[0] == "RMUX":
                        rmux_name, start_x, start_y, bit_width = start[1:]

                    if end[0] == "SB":
                        track1, end_x, end_y, side, io_, bit_width = end[1:]
                    elif end[0] == "PORT":
                        port_name, end_x, end_y, bit_width = end[1:]
                    elif end[0] == "REG":
                        reg_name, track1, end_x, end_y, bit_width = end[1:]
                    elif end[0] == "RMUX":
                        rmux_name, end_x, end_y, bit_width = end[1:]

                    if start_x == end_x and start_y == end_y:
                        wont_sort = True

                    segments_unsorted.append(((start_x,start_y),(end_x,end_y)))
                    if str((start_x,start_y)) not in segments_dict:
                        segments_dict[str((start_x,start_y))] = [segment]
                    else:
                        segments_dict[str((start_x,start_y))].append(segment)

                if not wont_sort:
                    g = Graph()
                    for seg in segments_unsorted:
                        src_id = str(seg[0])
                        sink_id = str(seg[1])
                        src_node = g.get_node(src_id)
                        sink_node = g.get_node(sink_id)
                        src_node.add_next("0", "0", sink_node)

                    segments_sorted = []
                    for node in g.sort():                    
                        if str(node) in segments_dict:
                            for segment in segments_dict[str(node)]:
                                if segment not in segments_sorted:
                                    segments_sorted.append(segment)

                    self.raw_routing_result[net_id] = segments_sorted


    def draw_grid(self, draw):
        draw.rectangle((0, self.img_width, 0, self.img_height), fill = (0, 0, 0, 255))
        for i in range(0, self.height + 1):
            # horizontal lines
            draw.line((0, i * self.scale, self.img_width, i * self.scale),
                    fill=(255, 255, 255), width=1)
            draw.text((0, i * self.scale), str(i))
                    
        for i in range(0, self.width + 1):
            # vertical lines
            draw.line((i * self.scale, 0, i * self.scale, self.img_height),
                    fill=(255, 255, 255), width=1)
            draw.text((i * self.scale, 0), str(i))

    def draw_routes(self, draw, crit_net = None):

        for route in self.unordered_routes:
            # if route['bit_width'] == 16:
            #     continue
            if crit_net == None or route["edge_id"] in crit_net:
                if crit_net != None and route["edge_id"] in crit_net:
                    color = lambda : (255, 0, 0, 255)
                else:
                    color = lambda : (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255), 255)
                route_color = color()
                for idx, seg1 in enumerate(route["segments"]):
                    if len(route["segments"]) > idx + 1:
                        seg2 = route["segments"][idx + 1]
                    else:
                        continue
                    x1 = seg1['x'] 
                    y1 = seg1['y']
                    x2 = seg2['x']
                    y2 = seg2['y']
                    track = seg2['track']
                    track4 = seg1['track']

                    if x1 != x2 and y1 != y2:
                        continue

                    end_offset = 0.5
                    start_offset = 0.5

                    if len(route["segments"]) > idx + 2:
                        seg3 = route["segments"][idx + 2]
                        track3 = seg3['track']

                        change_dir = not ((x1 == x2 == seg3['x']) or (y1 == y2 == seg3['y']))

                        # Assuming if route changes track its changing direction too
                        if track != track3 or change_dir:
                            end_offset = (track3 / self.num_tracks) * 0.6 + 0.2

                    change_dir = False
                    if idx > 0:
                        change_dir = not ((x1 == x2 == route["segments"][idx - 1]['x']) or (y1 == y2 == route["segments"][idx - 1]['y']))


                    # Assuming if route changes track its changing direction too
                    if track != track4 or change_dir:
                        start_offset = (track4 / self.num_tracks) * 0.6 + 0.2

                    track_offset = (track / self.num_tracks) * 0.6

                    if route['bit_width'] == 1:
                        route_width = 2
                    else:
                        route_width = 4

                    if x1 == x2:
                        # Vertical trace
                        # draw.line(((x1 + 0.2 + track_offset) * scale, (y1 + start_offset) * scale, (x2 + 0.2 + track_offset) * scale, (y2 + end_offset) * scale), fill=route_color, width=2)
                        arrowedLine(draw, ((x1 + 0.2 + track_offset) * self.scale, (y1 + start_offset) * self.scale), ((x2 + 0.2 + track_offset) * self.scale, (y2 + end_offset) * self.scale), color=route_color, size=route_width)
                    else:
                        # Horizontal trace
                        # draw.line(((x1 + start_offset) * self.scale, (y1 + 0.2 + track_offset) * self.scale, (x2 + end_offset) * self.scale, (y2 + 0.2 + track_offset) * self.scale), fill=route_color, width=2)
                        arrowedLine(draw,((x1 + start_offset) * self.scale, (y1 + 0.2 + track_offset) * self.scale), ((x2 + end_offset) * self.scale, (y2 + 0.2 + track_offset) * self.scale), color=route_color, size=route_width)

    def draw_tiles(self, draw):
        board_pos = self.raw_placement_result
        blk_id_list = list(board_pos.keys())
        blk_id_list.sort(key=lambda x: 0 if x[0] == "r" or x[0] == "i" else 1)
        for blk_id in blk_id_list:
            pos = board_pos[blk_id]
            index = self.color_index.index(blk_id[0])
            color = self.color_palette[index]


            width_frac = 1
            size = self.scale - 1
            width = size * width_frac
            shrink = self.scale/5 
            x, y = pos

            
            draw.rectangle((x * self.scale + 1 + shrink, y * self.scale + 1 + shrink, x * self.scale + width - shrink,
                        y * self.scale + size - shrink), fill=color)
            draw.text((x * self.scale + 1 + shrink, y * self.scale + 1 + shrink), blk_id)

            if blk_id in self.pe_reg:
                color = self.color_palette[self.color_index.index("r")]
                width_frac = 1
                size = self.scale - 1
                width = size * width_frac
                shrink = self.scale/2
                shrink2 = self.scale/5 
                x, y = pos
                draw.rectangle((x * self.scale + 1 + shrink2, y * self.scale + 1 + shrink, x * self.scale + width - shrink,
                            y * self.scale + size - shrink2), fill=color)

def visualize_pnr():
    placement_file, routing_file, folded_file, height, width, crit_net = parse_args()

    raw_routing_result = load_routing_result(routing_file)
    raw_placement_result = load_placement(placement_file)
    pe_reg = load_folded_regs(folded_file)
    pe_reg = {r for r,p in pe_reg}

    color_index = "imoprcdI"
    color_palette = [(166, 206, 227),
                (31, 120, 180),
                (178, 223, 138),
                (51, 160, 44),
                (251, 154, 153),
                (227, 26, 28),
                (253, 191, 111),
                (255, 127, 0),
                (202, 178, 214),
                (106, 61, 154),
                (255, 255, 153),
                (177, 89, 40)]

    scale = 60
    img_width = width * scale
    img_height = height * scale
    num_tracks = 5

    port_map = {}
    port_map["stencil_valid"] = "MEM"
    port_map["data_out_0"] = "MEM"
    port_map["data_out_1"] = "MEM"
    port_map["data_in_0"] = "MEM"
    port_map["data_in_1"] = "MEM"
    port_map["flush"] = "MEM"
    port_map["f2io_1"] = "IO1"
    port_map["io2f_1"] = "IO1"
    port_map["f2io_16"] = "IO16"
    port_map["io2f_16"] = "IO16"

    visualizer = Visualizer(img_width, img_height, width, height, scale, num_tracks, raw_routing_result, raw_placement_result, port_map, color_index, color_palette, pe_reg)

    visualizer.parse_raw_routing_result()

    visualizer.sort_segments()

    # ordered_routes, visited_points = sort_routes(routes_list)
   
    im = Image.new("RGBA", (img_width, img_height), "BLACK")
    draw = ImageDraw.Draw(im)

    visualizer.draw_grid(draw)

    visualizer.draw_routes(draw)

    visualizer.draw_tiles(draw)

    if crit_net != None:
        visualizer.draw_routes(draw, crit_net)

    im.save(f'pnr_result.png', format='PNG')


if __name__ == "__main__":
    sys.path.append(os.path.dirname(os.path.realpath(__file__)))
    visualize_pnr()