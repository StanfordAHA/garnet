import coreir
from .cyclone import InterconnectGraph, SwitchBoxSide, SwitchBoxIO, Node,\
    RegisterMuxNode, Tile, SwitchBoxNode, RegisterNode
import os
from typing import Dict, List, Tuple, Set, Union


def get_node_from_tile(graphs: Dict[int, InterconnectGraph],
                       coreir_node: List[str]):
    assert len(coreir_node) >= 2
    tile_str = coreir_node[0]
    node_str = coreir_node[1]

    x, y = get_tile_coord(tile_str)

    return get_node(graphs, node_str, x, y)


def get_node(graphs: Dict[int, InterconnectGraph],
             node_str: Union[str, Tuple[str]],
             x: int,
             y: int) -> Node:
    if isinstance(node_str, str):
        node_info = node_str.split("_")
    else:
        assert isinstance(node_str, list)
        node_info = node_str
    if node_info[0] == "WIRE" or node_info[0] == "MUX":
        # pass through wire and actual mux
        node_info.pop(0)
    node_type = node_info[0]

    # common routine
    bit_width_str = node_info[-1]
    assert bit_width_str[0] == "B"
    bit_width = int(bit_width_str[1:])
    assert bit_width in graphs
    graph = graphs[bit_width]
    tile = graph.get_tile(x, y)

    if node_type == "SB":
        assert len(node_info) == 6
        assert node_info[3] == "SB"
        node_info.pop(0)
        track_str = node_info[0]
        assert track_str[0] == "T"
        track_num = int(track_str[1:])
        side_str = node_info[1]
        node_side = SwitchBoxSide[side_str]
        node_io_str = node_info[2] + "_" + node_info[3]
        node_io = SwitchBoxIO[node_io_str]
        sb_node = tile.get_sb(node_side, track_num, node_io)
        return sb_node
    elif node_type == "REG":
        assert len(node_info) == 4
        reg_name = f"{node_info[1]}_{node_info[2]}"
        return tile.switchbox.registers[reg_name]
    elif node_type == "RMUX":
        node_info.pop(0)
        track_str = node_info[0]
        assert track_str[0] == "T"
        track_num = int(track_str[1:])
        side_str = node_info[1]
        node_side = SwitchBoxSide[side_str]
        mux_name = f"{node_side}_{track_num}"
        return tile.switchbox.reg_muxs[mux_name]
    else:
        raise NotImplementedError(node_str)


def get_tile_coord(tile_str):
    _, x_str, y_str = tile_str.split("_")
    # check the naming rules used in the RTL generator
    assert x_str[0] == "X"
    assert y_str[0] == "Y"
    x = int(x_str[1:], 16)
    y = int(y_str[1:], 16)
    return x, y


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


def has_pipeline_register(sb_node: SwitchBoxNode)\
        -> Tuple[bool, Union[RegisterMuxNode, None]]:
    if len(sb_node) == 2:
        reg_mux_node: RegisterMuxNode = None
        reg: RegisterNode = None
        for node in sb_node:
            if isinstance(node, RegisterMuxNode):
                reg_mux_node = node
            elif isinstance(node, RegisterNode):
                reg = node
        return reg is not None and reg_mux_node is not None, reg_mux_node
    return False, None


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
        is_pipelined, reg_mux_node = has_pipeline_register(sb_node)
        if is_pipelined:
            for node in reg_mux_node:
                if node.x != sb_node.x or node.y != sb_node.y:
                    find_node_conn_in_rtl(sb_node, node, tile_connections)
                    checked_node_connection.add((reg_mux_node, node))


def verify_tile_lift_connection(graphs: Dict[int, InterconnectGraph],
                                tile_module: coreir.module.Module,
                                tile_name: str):
    # this function checks if the port lifting is working properly
    # the checking logic is very similar to that of the inter-level
    x, y = get_tile_coord(tile_name)
    connections = tile_module.directed_module.connections
    lifted_connections = []
    for conn in connections:
        src, dst = conn.source, conn.sink
        if src[0] == "self" or dst[0] == "self":
            lifted_connections.append((src, dst))
    for bit_width, graph in graphs.items():
        tile = graph.get_tile(x, y)
        # we know that only switch box can go out of the tile
        # need to be careful about the pipeline registers
        switchbox = tile.switchbox
        sbs = switchbox.get_all_sbs()
        switchbox_name = get_sb_name(lifted_connections, switchbox)

        for sb_node in sbs:
            if sb_node.io == SwitchBoxIO.SB_IN:
                for node in sb_node:
                    assert node.x == x and node.y == y
                # making sure that tile has port lifted up
                found = False
                sb_name = str(sb_node)
                # very like turn into a pass through wire
                wire_sb_name = f"WIRE_{sb_name}"
                # thi following code is to break long binary ops statement
                # that PEP8 doesn't like
                for src, dst in lifted_connections:
                    if src[0] == "self" and src[1] == sb_name:
                        if dst[0] == switchbox_name and dst[1] == sb_name:
                            found = True
                            break
                        elif wire_sb_name == dst[0]:
                            found = True
                            break
                assert found, "ERROR in hardware generation"
            else:
                # even if it has pipeline register, we used the sb_name for
                # consistence. this saves us some trouble here
                found = False
                sb_name = str(sb_node)
                for src, dst in lifted_connections:
                    if dst[0] == "self" and dst[1] == sb_name:
                        if src[0] == switchbox_name and src[1] == sb_name:
                            found = True
                            break
                assert found, "ERROR in hardware generation"


def get_sb_name(connections, switchbox):
    prefix = f"SB_ID{switchbox.id}_{switchbox.num_track}TRACKS_" \
        f"B{switchbox.width}_"
    full_name = ""
    for src, dst in connections:
        if prefix in src[0]:
            full_name = src[0]
            break
        elif prefix in dst[0]:
            full_name = dst[0]
            break
    assert full_name != "", "Could not find " + prefix
    return full_name


def verify_sb_rtl(graphs: Dict[int, InterconnectGraph],
                  tile_module: coreir.module.Module,
                  tile_name: str,
                  checked_node_connection: Set[Tuple[Node, Node]]):
    # find every switchbox in the tile
    instances = tile_module.definition.instances
    connections = [(conn.source, conn.sink) for conn in
                   tile_module.directed_module.connections]
    switchbox_modules = {}
    for instance in instances:
        if instance.name[:2] == "SB":
            # it's a switch box
            switchbox_modules[instance.name] = instance.module
    x, y = get_tile_coord(tile_name)
    for _, graph in graphs.items():
        tile = graph.get_tile(x, y)
        switchbox_name = get_sb_name(connections, tile.switchbox)
        # filter all the connections being made to that switch box
        sb_connections = [(conn.source, conn.sink) for conn in
                          (switchbox_modules[switchbox_name]
                              .directed_module.connections)]
        # filter connections for sb nodes
        # we will verify pipeline registers as well
        node_connections = [(src, dst) for (src, dst) in sb_connections if
                            src[0] != "self" and dst[0] != "self"]
        # filter these we are interested in
        node_connections_ = []
        for src, dst in node_connections:
            tags = {"REG", "RMUX", "WIRE", "MUX"}
            src_split = src[0].split("_")
            dst_split = dst[0].split("_")
            src_tag = src_split[0]
            dst_tag = dst_split[0]
            last_src_tag = src_split[-1]
            if last_src_tag == "sel":
                # not concerned with sel for now
                continue
            if src_tag in tags and dst_tag in tags:
                if len(dst) == 3:
                    assert dst[1] == "I"
                    index = int(dst[-1])
                else:
                    index = 0
                node_connections_.append((src[0], dst[0], index))
        for src, dst, index in node_connections_:
            src_node = get_node(graphs, src, x, y)
            dst_node = get_node(graphs, dst, x, y)
            assert dst_node in src_node
            # check the index is correct as well
            assert index == dst_node.get_conn_in().index(src_node)
            checked_node_connection.add((src_node, dst_node))

        # the last, verify some other logistics connections
        # not for the cyclone graph
        node_connections_ = []
        for src, dst in node_connections:
            src_split = src[0].split("_")
            last_src_tag = src_split[-1]
            if last_src_tag == "sel" and "Zext" not in dst[0]:
                # not concerned with sel for now
                node_connections_.append((src[0], dst[0]))
        for _, dst in node_connections_:
            dst_node = get_node(graphs, dst, x, y)
            # only multiple incoming edges will have selection
            assert len(dst_node.get_conn_in()) > 1


def check_graph_isomorphic(graphs: Dict[int, InterconnectGraph], filename: str):
    assert os.path.isfile(filename)
    context = coreir.Context()
    context.load_library('commonlib')
    mod = context.load_from_file(filename)
    tile_modules = {}
    for instance in mod.definition.instances:
        assert instance.name == instance.selectpath[0]
        if instance.name[:4] == "Tile":
            tile_modules[instance.name] = instance.module

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
        src_node = get_node_from_tile(graphs, src)
        dst_node = get_node_from_tile(graphs, dst)
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
    # this is not part of the graph isomorphism check, yet it's very
    # important that ports lifted to the tile level are actually connected
    for tile_name, tile_module in tile_modules.items():
        verify_tile_lift_connection(graphs, tile_module, tile_name)

    # CHECK 3
    # after verifying the inter-tile connections, we need to check if the
    # switch box is created correctly. This will cover pipeline register check
    # verify RTL -> cyclone
    for tile_name, tile_module in tile_modules.items():
        verify_sb_rtl(graphs, tile_module, tile_name, checked_node_connection)

    # verify cyclone -> RTL

    # CHECK 3:
    # This is to check if the port connection is correct, this means to check
    # port <-> CB/SB in both internal module and module connection
    # (due to port lifting)
