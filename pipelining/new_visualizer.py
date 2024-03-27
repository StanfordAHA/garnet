import random
import sys
from PIL import Image, ImageDraw
from archipelago.io import load_routing_result
from pycyclone.io import load_placement
import math
import os
import argparse
from typing import Dict, List, Tuple, Set
#from .place_and_route_graph import construct_graph, load_folded_regs

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

class RouteNode:
    def __init__(self, node_id = 0, x = 0, y = 0, track = 0, net_id = 0, bit_width = 0):
        self.node_id = node_id
        self.x = x
        self.y = y
        self.track = track
        self.net_id = net_id
        self.bit_width = bit_width

class Route:
    def __init__(self, prev_node = None, node = None, continue_route = False, route_dir = None):
        self.prev_node = prev_node
        self.node = node
        self.continue_route = continue_route
        self.route_dir = route_dir


class Visualizer():
    def __init__(self, img_width, img_height, width, height, scale, num_tracks, graph, color_index, color_palette):
        self.img_width = img_width 
        self.img_height = img_height 
        self.width = width 
        self.height = height 
        self.scale = scale
        self.num_tracks = num_tracks
        self.graph = graph
        self.color_index = color_index
        self.color_palette = color_palette

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



    def topological_sort(self):
        stack = []
        routes = []
        for n in self.graph.inputs:
            self.topological_sort_helper(n, stack, routes)
        return stack[::-1]

    def topological_sort_helper(self, node: str, stack, routes):

        for ns in self.graph.sinks[node]:
            self.topological_sort_helper(ns, stack, routes)

        new_node = RouteNode()
        new_node.node_id = node
        new_node.x = node.x
        new_node.y = node.y
        new_node.track = node.track
        new_node.net_id  = node.net_id
        new_node.bit_width = node.bit_width


        if self.graph.get_node(node).type_ == "route" and self.graph.get_node(node).track != None:
            if len(stack) != 0:
                prev_node = stack[-1]

                if prev_node.net_id == new_node.net_id:
                    if ((new_node.x - prev_node.x) + (new_node.y - prev_node.y) == 1):
                        new_route = Route()
                        new_route.prev_node = prev_node
                        new_route.node = new_node
                        new_route.route_dir = "x" if new_node.y == prev_node.y else "y"
                        
                        if len(routes) > 0:
                            new_route.continue_route = routes[-1][1].net_id == new_node.net_id

                        routes.append((prev_node, new_node))
                        stack.append(new_node)
                else:
                    stack.append(new_node)
            
            else:
                stack.append(new_node)

    def draw_routes(self, draw, crit_net = None):
        color = lambda : (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255), 255)
        net_colors = {}
        for node in self.graph.nodes:
            net_id = self.graph.get_node(node).net_id
            if crit_net != None:
                if net_id in crit_net:
                    net_colors[net_id] = (255, 0, 0, 255)
            else:
                net_colors[net_id] = color()

        for edge in self.graph.edges:
            src_node = self.graph.get_node(edge[0])
            dst_node = self.graph.get_node(edge[1])

            if src_node.type_ == 'tile' or dst_node.type_ == 'tile':
                continue

            if src_node.x == dst_node.x and src_node.y == dst_node.y:
                continue

            if src_node.net_id not in net_colors:
                continue
            
            route_color = net_colors[src_node.net_id]

            x1 = src_node.x
            y1 = src_node.y
            x2 = dst_node.x
            y2 = dst_node.y
            track = src_node.track
            end_offset = 0.5
            start_offset = 0.5

            if track == None:
                track = dst_node.track
                if track == None:
                    # Hacky, but we need to look back to the last SB to find the track for this connection
                    # track = self.get_prev_track(edge[0])
                    track = 0


            # # start offset first
            # self.get_prev_track(edge[0])
            # if len(self.graph.sources[edge[0]]) > 0:
            #     changed_track = self.graph.get_node(self.graph.sources[edge[0]][0]).track

            #     if changed_track != None:
            #         start_offset = (int(changed_track) / self.num_tracks) * 0.6


            # if len(route["segments"]) > idx + 2:
            #     seg3 = route["segments"][idx + 2]
            #     track3 = seg3['track']

            #     change_dir = not ((x1 == x2 == seg3['x']) or (y1 == y2 == seg3['y']))

            #     # Assuming if route changes track its changing direction too
            #     if track != track3 or change_dir:
            #         end_offset = (track3 / self.num_tracks) * 0.6 + 0.2

            # change_dir = False
            # if idx > 0:
            #     change_dir = not ((x1 == x2 == route["segments"][idx - 1]['x']) or (y1 == y2 == route["segments"][idx - 1]['y']))


            # # Assuming if route changes track its changing direction too
            # if track != track4 or change_dir:
            #     start_offset = (track4 / self.num_tracks) * 0.6 + 0.2

            track_offset = (int(track) / self.num_tracks) * 0.6
            
            if src_node.bit_width == 1:
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
        # board_pos = self.graph.nodes
        # blk_id_list = list(board_pos.keys())
        # blk_id_list.sort(key=lambda x: 0 if x[0] == "r" or x[0] == "i" else 1)
        for blk_id in self.graph.nodes:
            node = self.graph.get_node(blk_id)

            if node.type_ == "route":
                continue

            index = self.color_index.index(blk_id[0])
            color = self.color_palette[index]


            width_frac = 1
            size = self.scale - 1
            width = size * width_frac
            shrink = self.scale/5 
            x, y = node.x, node.y

            
            draw.rectangle((x * self.scale + 1 + shrink, y * self.scale + 1 + shrink, x * self.scale + width - shrink,
                        y * self.scale + size - shrink), fill=color)
            draw.text((x * self.scale + 1 + shrink, y * self.scale + 1 + shrink), blk_id)

            for src in self.graph.sources[blk_id]:
                if self.graph.get_node(src).reg:
                    color = self.color_palette[self.color_index.index("r")]
                    width_frac = 1
                    size = self.scale - 1
                    width = size * width_frac
                    shrink = self.scale/2
                    shrink2 = self.scale/5 
                    draw.rectangle((x * self.scale + 1 + shrink2, y * self.scale + 1 + shrink, x * self.scale + width - shrink,
                                y * self.scale + size - shrink2), fill=color)

def visualize_pnr(graph, crit_net):

    width = 0
    height = 0
    for node in graph.nodes:
        width = max(width, graph.get_node(node).x)
        height = max(height, graph.get_node(node).y)
    width += 1
    height += 1


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

    visualizer = Visualizer(img_width, img_height, width, height, scale, num_tracks, graph, color_index, color_palette)

    # visualizer.parse_raw_routing_result()

    # visualizer.sort_segments()

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
