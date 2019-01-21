from common.core import Core
from typing import Tuple, List, Dict, Callable
from .cyclone import SwitchBoxSide, SwitchBoxIO, InterconnectPolicy
from .cyclone import InterconnectGraph, DisjointSwitchBox, WiltonSwitchBox
from .cyclone import ImranSwitchBox, Tile
from .circuit import CoreInterface
from pe_core.pe_core_magma import PECore
from memory_core.memory_core_magma import MemCore
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
                                sb_type: SwitchBoxType) -> InterconnectGraph:
    """Create a uniform interconnect with column-based design. We will use
    disjoint switch for now. Configurable parameters in terms of interconnect
    design:
        1. how ports are connected via switch box or connection box
        2. the distribution of various L1/L2/L4 etc. wiring segments
        3. internal switch design, e.g. wilton and Imran.

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
                sb = DisjointSwitchBox(x, y, track_width, num_track)
            elif sb_type == SwitchBoxType.Wilton:
                sb = WiltonSwitchBox(x, y, track_width, num_track)
            elif sb_type == SwitchBoxType.Imran:
                sb = ImranSwitchBox(x, y, track_width, num_track)
            else:
                raise NotImplementedError(sb_type)
            tile_circuit = Tile(x, y, width, sb, tile_height)

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

    return interconnect


def create_simple_cgra(width: int, height: int):
    # we create both 1-bit and 16-bit interconnect
    bit_widths = (1, 16)
    num_track = 5
    track_info = {1: num_track}

    def create_core(x: int, _: int) -> Core:
        # we're not doing anything with IO and other stuff so taking in x
        # coord is sufficient
        if x % 4 == 3:
            return MemCore(16, 1024)
        else:
            return PECore()

    # create connections
    # for current CGRA, outputs go to every side and inputs are biased
    # we need to take care of biased connections
    port_conns = {}

    # all sides and out
    all_out = ["res", "resp", "rdata", "valid"]
    # bit0, data0, wdata, and wen only comes from the Left (West) side
    left = ["data0", "bit0", "wdata", "wen"]
    # ren, bit1 and data1 only comes from the Bottom (South) side
    bottom = ["wen", "data1", "bit1"]
    # bit2 can only comes from the Top (North) side
    top = ["bit2"]

    # outputs
    for side in SwitchBoxSide:
        for port_name in all_out:
            port_conns[port_name].append((side, SwitchBoxIO.SB_OUT))

    # inputs
    for io in SwitchBoxIO:
        for port_name in left:
            port_conns[port_name].append((SwitchBoxSide.WEST, io))

        for port_name in bottom:
            port_conns[port_name].append((SwitchBoxSide.SOUTH, io))

        for port_name in top:
            port_conns[port_name].append((SwitchBoxSide.NORTH, io))

    result: List[InterconnectGraph] = [None] * len(bit_widths)
    for idx, bit_width in enumerate(bit_widths):
        result[idx] = create_uniform_interconnect(width, height, bit_width,
                                                  create_core, port_conns,
                                                  track_info,
                                                  SwitchBoxType.Disjoint)

    return result
