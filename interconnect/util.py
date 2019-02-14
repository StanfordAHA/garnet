from common.core import Core
from typing import Tuple, List, Dict, Callable
from .cyclone import SwitchBoxSide, SwitchBoxIO, InterconnectPolicy, \
    InterconnectGraph, DisjointSwitchBox, WiltonSwitchBox, \
    ImranSwitchBox, Tile, SwitchBox
from .circuit import CoreInterface
import enum


@enum.unique
class SwitchBoxType(enum.Enum):
    Disjoint = enum.auto()
    Wilton = enum.auto()
    Imran = enum.auto()


def compute_num_tracks(x_offset: int, y_offset: int,
                       x: int, y: int, track_info: Dict[int, int]):
    """compute the num of tracks needed for (x, y), given the track
    info"""
    x_diff = x - x_offset
    y_diff = y - y_offset
    result = 0
    for length, num_track in track_info.items():
        if x_diff % length == 0 and y_diff % length == 0:
            # it's the tile
            result += num_track
    return result


# helper functions to create column-based CGRA interconnect
# FIXME: allow IO tiles being created
def create_uniform_interconnect(width: int,
                                height: int,
                                track_width: int,
                                column_core_fn: Callable[[int, int], Core],
                                port_connections:
                                Dict[str, List[Tuple[SwitchBoxSide,
                                                     SwitchBoxIO]]],
                                track_info: Dict[int, int],
                                sb_type: SwitchBoxType,
                                pipeline_reg:
                                List[Tuple[int, SwitchBoxSide]] = None,
                                margin: int = 0
                                ) -> InterconnectGraph:
    """Create a uniform interconnect with column-based design. We will use
    disjoint switch for now. Configurable parameters in terms of interconnect
    design:
        1. how ports are connected via switch box or connection box
        2. the distribution of various L1/L2/L4 etc. wiring segments
        3. internal switch design, e.g. wilton and Imran.
        4. automatic pipeline register insertion

    :parameter width: width of the interconnect
    :parameter height: height of the interconnect
    :parameter track_width: width of the track, e.g. 16 or 1
    :parameter column_core_fn: a function that returns Core at (x, y)
    :parameter port_connections: specifies the core port connection types,
                                 indexed by port_name
    :parameter track_info: specifies the track length and the number of each.
                           e.g. {1: 4, 2: 1} means L1 segment for 4 tracks and
                           L2 segment for 1 track
    :parameter sb_type: Switch box type.
    :parameter pipeline_reg: specifies which track and which side to insert
                             pipeline registers
    :parameter margin: PE/MEM margin, can only be 0 or 1

    :return configured Interconnect object
    """
    assert margin in (0, 1), "margin can either be 0 or 1"
    tile_height = 1
    x_offset = margin
    y_offset = margin
    interconnect = InterconnectGraph(track_width)
    # create tiles and set cores
    for x in range(x_offset, width - x_offset + margin):
        for y in range(y_offset, height - y_offset, tile_height + margin):
            # compute the number of tracks
            num_track = compute_num_tracks(x_offset, y_offset,
                                           x, y, track_info)
            # create switch based on the type passed in
            if sb_type == SwitchBoxType.Disjoint:
                sb = DisjointSwitchBox(x, y, num_track, track_width)
            elif sb_type == SwitchBoxType.Wilton:
                sb = WiltonSwitchBox(x, y, num_track, track_width)
            elif sb_type == SwitchBoxType.Imran:
                sb = ImranSwitchBox(x, y, num_track, track_width)
            else:
                raise NotImplementedError(sb_type)
            tile_circuit = Tile(x, y, track_width, sb, tile_height)

            interconnect.add_tile(tile_circuit)
            core = column_core_fn(x, y)
            core_interface = CoreInterface(core)
            interconnect.set_core(x, y, core_interface)

    # create tiles without SB
    for x in range(width + 2 * margin):
        for y in range(height + 2 * margin):
            # skip if the tiles is already created
            tile = interconnect.get_tile(x, y)
            if tile is not None:
                continue
            # empty switch box
            sb = SwitchBox(x, y, 0, track_width, [])
            tile_circuit = Tile(x, y, track_width, sb, tile_height)
            interconnect.add_tile(tile_circuit)
            core = column_core_fn(x, y)
            core_interface = CoreInterface(core)
            interconnect.set_core(x, y, core_interface)

    # set port connections
    for port_name, conns in port_connections.items():
        interconnect.set_core_connection_all(port_name, conns)
    # set the actual interconnections
    # sort the tracks by length
    track_lens = list(track_info.keys())
    track_lens.sort()
    current_track = 0
    for track_len in track_lens:
        for _ in range(track_info[track_len]):
            interconnect.connect_switchbox(x_offset, y_offset, width + x_offset,
                                           height + y_offset,
                                           track_len,
                                           current_track,
                                           InterconnectPolicy.Ignore)
            current_track += 1

    # insert pipeline register
    if pipeline_reg is None:
        pipeline_reg = []
    for track, side in pipeline_reg:
        for coord in interconnect:
            tile = interconnect[coord]
            if track < tile.switchbox.num_track:
                tile.switchbox.add_pipeline_register(side, track)

    return interconnect


def connect_io(interconnect: InterconnectGraph,
               input_port_conn: Dict[str, List[int]],
               output_port_conn: Dict[str, List[int]]):
    """connect tiles on the margin"""
    margin = 1
    x_max, y_max = interconnect.get_size()
    # compute tiles and sides
    for x in range(x_max):
        for y in range(y_max):
            if x in range(margin, x_max - margin) or \
                    y in range(margin, y_max - margin):
                continue
            # make sure that these margins tiles have empty switch boxes
            tile = interconnect[(x, y)]
            assert tile.switchbox.num_track == 0
            # compute the nearby tile
            if x in range(0, margin):
                next_tile = interconnect[(x + 1, y)]
                side = SwitchBoxSide.WEST
            elif x in range(x_max - margin, x_max):
                next_tile = interconnect[(x - 1, y)]
                side = SwitchBoxSide.EAST
            elif y in range(0, margin):
                next_tile = interconnect[(x, y + 1)]
                side = SwitchBoxSide.NORTH
            else:
                assert y in range(y_max - margin, y_max)
                next_tile = interconnect[(x, y - 1)]
                side = SwitchBoxSide.SOUTH
            for input_port, conn in input_port_conn.items():
                # input is one to all connection
                if input_port in tile.ports:
                    port_node = tile.ports[input_port]
                    for track in conn:
                        # to be conservative when connecting the nodes
                        if track < next_tile.switchbox.num_track:
                            sb_node = next_tile.get_sb(side, track,
                                                       SwitchBoxIO.SB_IN)
                            port_node.add_edge(sb_node)
            for output_port, conn in output_port_conn.items():
                if output_port in tile.ports:
                    port_node = tile.ports[output_port]
                    for track in conn:
                        if track < next_tile.switchbox.num_track:
                            sb_node = next_tile.get_sb(side, track,
                                                       SwitchBoxIO.SB_IN)
                            port_node.add_edge(sb_node)
