from common.core import Core
from typing import Tuple, List, Dict, Callable
from .cyclone import SwitchBoxSide, SwitchBoxIO, InterconnectPolicy
from .cyclone import InterconnectGraph, DisjointSwitchBox, WiltonSwitchBox
from .cyclone import ImranSwitchBox, Tile
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
                                List[Tuple[int, SwitchBoxSide]] = None
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

    :return configured Interconnect object
    """
    tile_height = 1
    x_offset = 0
    y_offset = 0
    interconnect = InterconnectGraph(track_width)
    # create tiles and set cores
    for x in range(x_offset, width - x_offset):
        for y in range(y_offset, height - y_offset, tile_height):
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
            interconnect.connect_switchbox(x_offset, y_offset, width, height,
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
