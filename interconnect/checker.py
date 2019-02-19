import coreir
from .cyclone import InterconnectGraph, SwitchBoxSide, SwitchBoxIO, Node,\
    RegisterMuxNode, Tile, SwitchBoxNode
import os
from typing import Dict, List, Tuple, Set


def get_node(graphs: Dict[int, InterconnectGraph], coreir_node: List[str]):
    assert len(coreir_node) >= 2
    tile_str = coreir_node[0]
    node_str = coreir_node[1]

    _, x_str, y_str = tile_str.split("_")
    # check the naming rules used in the RTL generator
    assert x_str[0] == "X"
    assert y_str[0] == "Y"
    x = int(x_str[1:], 16)
    y = int(y_str[1:], 16)

    # parse the node_str
    node_info = node_str.split("_")
    assert len(node_info) == 6
    assert node_info[0] == "SB" and node_info[3] == "SB"
    node_info.pop(0)
    track_str = node_info[0]
    assert track_str[0] == "T"
    track_num = int(track_str[1:])
    side_str = node_info[1]
    node_side = SwitchBoxSide[side_str]
    node_io_str = node_info[2] + "_" + node_info[3]
    node_io = SwitchBoxIO[node_io_str]
    bit_width_str = node_info[-1]
    assert bit_width_str[0] == "B"
    bit_width = int(bit_width_str[1:])

    # get the node
    assert bit_width in graphs
    graph = graphs[bit_width]
    tile = graph.get_tile(x, y)
    sb_node = tile.get_sb(node_side, track_num, node_io)
    return sb_node


def verify_inter_tile_connection_rtl(src_node: Node, dst_node: Node):
    # the goal is to verify that these two nodes are indeed "connection"
    # notice that due to the insertion of pipeline registers, they may not
    # be actually connected. However, we need to detect if that the case and
    # check the reg mux connection.
    if dst_node in src_node:
        # no pipeline registers
        return
    # making sure it's pipeline register mode
    assert len(src_node) == 2, f"{src_node} has to connected as pipeline " \
        f"register"
    nodes = list(src_node)
    # we will verify if the register is created properly later inside the
    # switchbox
    r_mux = nodes[0] if isinstance(nodes[0], RegisterMuxNode) else nodes[1]
    assert isinstance(r_mux, RegisterMuxNode)
    assert dst_node in r_mux, "Incorrect hardware generation"
    assert r_mux in dst_node.get_conn_in(), "Incorrect hardware generation"


def find_node_conn_in_rtl(src_node: Node, dst_node: Node,
                          tile_connections: List[Tuple[List[str], List[str]]]):
    src_tile_str = f"Tile_X{src_node.x:02X}_Y{src_node.y:02X}"
    src_node_str = str(src_node)
    dst_tile_str = f"Tile_X{dst_node.x:02X}_Y{dst_node.y:02X}"
    dst_node_str = str(dst_node)
    found = False
    for conn_src, conn_dst in tile_connections:
        if conn_src[0] == src_tile_str \
                and conn_src[1] == src_node_str \
                and conn_dst[0] == dst_tile_str \
                and conn_dst[1] == dst_node_str:
            found = True
            break
    assert found, "ERROR in hardware generation"


def verify_inter_tile_connection_cyclone(sb_nodes: List[SwitchBoxNode],
                                         tile_connections:
                                         List[Tuple[List[str], List[str]]],
                                         checked_node_connection:
                                         Set[Tuple[Node, Node]]):
    for sb_node in sb_nodes:
        if sb_node.io != SwitchBoxIO.SB_OUT:
            continue
        # for any out of tile connection directly
        for node in sb_node:
            if node.x != sb_node.x or node.y != sb_node.y:
                find_node_conn_in_rtl(sb_node, node, tile_connections)
                checked_node_connection.add((sb_node, node))
        # if there is pipeline registers, we check the reg mux
        if len(sb_node) == 2:
            reg_mux_node: RegisterMuxNode = None
            for node in sb_node:
                if isinstance(node, RegisterMuxNode):
                    reg_mux_node = node
            if reg_mux_node is not None:
                for node in reg_mux_node:
                    if node.x != sb_node.x or node.y != sb_node.y:
                        find_node_conn_in_rtl(sb_node, node, tile_connections)
                        checked_node_connection.add((reg_mux_node, node))


def check_graph_isomorphic(graphs: Dict[int, InterconnectGraph], filename: str):
    assert os.path.isfile(filename)
    context = coreir.Context()
    context.load_library('commonlib')
    mod = context.load_from_file(filename)
    instance_names = []
    for instance in mod.definition.instances:
        instance_names.append(instance.name)
        assert instance.name == instance.selectpath[0]

    # checked pairs from graph
    # because there are many connections un-related to the inter-connect
    # we hold account for every connection checked in the cyclone based ont he
    # RTL
    checked_node_connection: Set[Tuple[Node, Node]] = set()

    # CHECK 1:
    # we verify inter-tile connections first. making sure it's bijective
    tile_connections: List[Tuple[List[str], List[str]]] = []
    for conn in mod.directed_module.connections:
        src: List[str] = conn.source
        dst: List[str] = conn.sink
        src_name: str = src[0]
        dst_name: str = dst[0]
        src_node_name: str = src[1]
        dst_node_name: str = dst[1]
        if src_name[:4].lower() == "tile" and dst_name[:4].lower() == "tile" \
                and src_node_name[:2] == "SB" and dst_node_name[:2] == "SB":
            tile_connections.append((src, dst))

    # verify RTL -> cyclone
    for src, dst in tile_connections:
        src_node = get_node(graphs, src)
        dst_node = get_node(graphs, dst)
        assert src_node is not None, "ERROR in hardware creation"
        assert dst_node is not None, "ERROR in hardware creation"
        verify_inter_tile_connection_rtl(src_node, dst_node)

    # verify cyclone -> RTL
    for _, graph in graphs.items():
        for x, y in graph:
            tile: Tile = graph.get_tile(x, y)
            sb_nodes = tile.switchbox.get_all_sbs()
            verify_inter_tile_connection_cyclone(sb_nodes, tile_connections,
                                                 checked_node_connection)

    # CHECK 2
    # after verifying the inter-tile connections, we need to check if the
    # switch box is created correctly. This will cover pipeline register check

    # CHECK 3:
    # This is to check if the port connection is correct, this means to check
    # port <-> CB/SB in both internal module and module connection
    # (due to port lifting)
