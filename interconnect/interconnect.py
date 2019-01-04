import enum
import magma
import generator.generator as generator
from common.core import Core
from typing import Union, Tuple, NamedTuple, List, Dict, Callable
from .graph import SwitchBoxSide, SwitchBoxIO, Graph, Tile
from .graph import PortNode, SwitchBoxNode, Switch
from .sb import SB, SwitchBoxType, SwitchBoxHelper
from .muxblock import CB
import magma.bitutils

GridCoordinate = Tuple[int, int]


def get_width(t):
    if isinstance(t, magma.BitKind):
        return 1
    if isinstance(t, magma.BitsKind):
        return len(t)
    raise NotImplementedError(t, type(t))


class InterconnectType(enum.Enum):
    Mesh = 0
    Hierarchical = 1
    Hybrid = 2


# garnet's PEP 8 doesn't like the new way to declare named tuple with type
# hints using the old format
SBConnectionType = NamedTuple("SBConnectionType",
                              [("side", SwitchBoxSide),
                               ("track", int),
                               ("io", SwitchBoxIO)])


class InterconnectPolicy(enum.Enum):
    PassThrough = enum.auto()
    Ignore = enum.auto()


class Interconnect(generator.Generator):
    """This is the `traditional` sense of interconnect that doesn't deal with
    the global signals and clocks (since VPR doesnt do PnR on these signals
    either). We need a separate pass to produce global signals.
    The interconnect allows user to specify:
        1. Connection types for each port, i.e. SB (partly) and CB.
        2. Intra-connection types for each switch box, i.e. internal population
        3. Inter-connection types for switch box:
            a. variable length
            b. non-uniform routing resource
    """
    def __init__(self, track_width: int, connection_type: InterconnectType):
        super().__init__()
        self.track_width = track_width
        if connection_type != InterconnectType.Mesh:
            raise NotImplementedError("Only Mesh network is currently "
                                      "supported")
        self.graph_ = Graph()

        # this is a 2d grid consistent with the routing graph. it's designed
        # to support fast query with irregular tile height.
        self.grid_ = []

        # Note (keyi):
        # notice that these following statement will trigger garnet's travis
        # to report E701 error. However, it is allowed in the updated
        # pycodestyle and pyflakes. It is because the PEP8 checker used in
        # garnet is about 4 years old and deprecated long time ago.
        # I'd personally suggest to switch to more modern style checker.
        # I will continue to use such type hints because that's the only way
        # to do so.

        # placeholders for sb and cb
        self.sbs: Dict[Tuple[int, int], SB] = {}
        self.cbs: Dict[Tuple[int, int, str], CB] = {}

        self.tiles: Dict[Tuple[int, int], Tile] = {}

    def add_tile(self, tile: Tile) -> None:
        self.graph_.add_tile(tile)
        # adjusting grid_
        x = tile.x
        y = tile.y
        height = tile.height
        # automatically scale the chip
        while len(self.grid_) < y + height:
            self.grid_.append([])
        for row in range(len(self.grid_)):
            while len(self.grid_[row]) <= x:
                self.grid_[row].append(None)
        # store indices and checking for correctness
        self.__assign_grid(x, y, tile)
        for i in range(y + 1, y + height):
            self.__assign_grid(x, i, (x, y))

    def get_tile(self, x: int, y: int) -> Union[Tile, None]:
        width, height = self.get_size()
        if x >= width or y >= height:
            return None
        result = self.grid_[y][x]
        if isinstance(result, tuple):
            new_x, new_y = result
            return self.grid_[new_y][new_x]
        return result

    def has_empty_tile(self) -> bool:
        for y in range(len(self.grid_)):
            for x in range(len(self.grid_[y])):
                if self.grid_[y][x] is None:
                    return True
        return False

    def __assign_grid(self, x: int, y: int,
                      tile: Union[Tile, GridCoordinate]) -> None:
        self.__check_grid(x, y)
        self.grid_[y][x] = tile

    def __check_grid(self, x: int, y: int) -> None:
        if self.grid_[y][x] is not None:
            tile_index = self.grid_[y][x]
            if isinstance(tile_index, Tile):
                tile_name = tile_index.name()
            else:
                tile_name = self.grid_[tile_index[1]][tile_index[0]].name()
            raise RuntimeError(f"Tile ({x}, {y}) is assigned with " +
                               tile_name)

    def get_size(self) -> Tuple[int, int]:
        height = len(self.grid_)
        width = len(self.grid_[0])
        return width, height

    def set_core(self, x: int, y: int, core: Core):
        tile = self.get_tile(x, y)
        tile.set_core(core)

    def set_core_connection(self, x: int, y: int, port_name: str,
                            connection_type: List[SBConnectionType]):
        # we add a new port here
        tile = self.get_tile(x, y)
        # make sure that it's an input port
        is_input = tile.core_has_input(port_name)
        is_output = tile.core_has_output(port_name)

        if not (is_input ^ is_output):
            raise ValueError("core design error. " + port_name + " cannot be "
                             " both input and output port")

        port_node = PortNode(port_name, tile.x, tile.y, self.track_width)
        # add to graph node first, we will handle magma in a different pass
        # based on the graph, since we need to compute the mux height
        for side, track, io in connection_type:
            sb = SwitchBoxNode(tile.x, tile.y, self.track_width,
                               track, side.value, io.value)
            if is_input:
                self.connect(sb, port_node)
            else:
                self.connect(port_node, sb)

    def set_core_connection_all(self, port_name: str,
                                connection_type: List[Tuple[SwitchBoxSide,
                                                            SwitchBoxIO]]):
        """helper function to set connections for all the tiles with the
        same port_name"""
        width, height = self.get_size()
        for y in range(height):
            for x in range(width):
                tile = self.grid_[y][x]
                if isinstance(tile, Tile):
                    # construct the connection types
                    switch = tile.switchbox
                    num_track = switch.num_track
                    connections: List[SBConnectionType] = []
                    for track in num_track:
                        for side, io in connection_type:
                            connections.append(SBConnectionType(side, track,
                                                                io))
                    self.set_core_connection(x, y, port_name, connections)

    def connect(self, node_from, node_to):
        self.graph_.add_edge(node_from, node_to)

    def connect_switch(self, x0: int, y0: int, x1: int, y1: int,
                       expected_length: int, track: int,
                       policy: InterconnectPolicy):
        """connect switches with expected length in the region
        (x0, y0) <-> (x1, y1). it will tries to connect everything with
        expected length. connect in left -> right & top -> bottom fashion.

        policy:
            used when there is a tile with height larger than 1.
            PassThrough: allow to connect even if the wire length is different
                         from the expected_length. This will introduce
                         uncertainties of total wires and may introduce bugs.
                         one remedy for that is to break the tiles into smaller
                         tiles and assign switch box for each smaller tiles
            Ignore: ignore the connection if the wire length is different from
                    the expected_length. it is safe but may leave some tiles
                    unconnected
        """
        if x1 - expected_length <= x0 or y1 - expected_length <= y0:
            raise ValueError("the region has to be bigger than expected "
                             "length")

        if x1 - x0 % expected_length != 0:
            raise ValueError("the region x has to be divisible by expected_"
                             "length")
        if y1 - y0 % expected_length != 0:
            raise ValueError("the region y has to be divisible by expected_"
                             "length")

        # Note (keyi):
        # this code is very complex and hence has many comments. please do not
        # simplify this code unless you fully understand the logic flow.

        # left to right first
        for x in range(x0, x1 - expected_length, expected_length):
            for y in range(y0, y1, expected_length):
                if not isinstance(self.grid_[y][x], Tile):
                    continue
                tile_from = self.get_tile(x, y)
                tile_to = self.get_tile(x + expected_length, y)
                # several outcomes to consider
                # 1. tile_to is empty -> apply policy
                # 2. tile_to is a reference -> apply policy
                if tile_to is None or (not isinstance(tile_to, Tile)):
                    if policy & InterconnectPolicy.Ignore:
                        continue
                    # find another tile longer than expected length that's
                    # within the range. because at this point we already know
                    # that the policy is passing through, just search the
                    # nearest tile (not tile reference) to meet the pass
                    # through requirement
                    x_ = x
                    while x_ < x1:
                        if isinstance(self.grid_[y][x_], Tile):
                            tile_to = self.grid_[y][x_]
                            break
                        x_ += 1
                    # check again if we have resolved this issue
                    # since it's best effort, we will ignore if no tile left
                    # to connect
                    if tile_to is None or (not isinstance(tile_to, Tile)):
                        continue

                assert tile_to.y == tile_from.y
                # add to connection list
                # forward
                self.__add_sb_connection(tile_from, tile_to, track,
                                         SwitchBoxSide.EAST)

                # backward
                self.__add_sb_connection(tile_to, tile_from, track,
                                         SwitchBoxSide.WEST)

        # top to bottom this is very similar to the previous one (left to
        # right)
        for x in range(x0, x1):
            for y in range(y0, y1 - expected_length, expected_length):
                if not isinstance(self.grid_[y][x], Tile):
                    continue
                tile_from = self.get_tile(x, y)
                tile_to = self.get_tile(x, y + expected_length)
                # several outcomes to consider
                # 1. tile_to is empty -> apply policy
                # 2. tile_to is a reference -> apply policy
                if tile_to is None or (not isinstance(tile_to, Tile)):
                    if policy & InterconnectPolicy.Ignore:
                        continue
                    y_ = y
                    while y_ < y1:
                        if isinstance(self.grid_[y_][x], Tile):
                            tile_to = self.grid_[y_][x]
                            break
                        y_ += 1
                    # check again if we have resolved this issue
                    # since it's best effort, we will ignore if no tile left
                    # to connect
                    if tile_to is None or (not isinstance(tile_to, Tile)):
                        continue

                assert tile_to.x == tile_from.x
                # add to connection list
                # forward
                self.__add_sb_connection(tile_from, tile_to, track,
                                         SwitchBoxSide.SOUTH)
                # backward
                self.__add_sb_connection(tile_to, tile_from, track,
                                         SwitchBoxSide.NORTH)

    def __add_sb_connection(self, tile_from: Tile, tile_to: Tile, track: int,
                            side: SwitchBoxSide):
        # connect the underlying routing graph
        sb_from = SwitchBoxNode(tile_from.x, tile_from.y,
                                self.track_width,
                                track,
                                side,
                                SwitchBoxIO.OUT)
        sb_to = SwitchBoxNode(tile_to.x, tile_to.y,
                              self.track_width,
                              track,
                              SwitchBoxSide.get_opposite_side(side),
                              SwitchBoxIO.IN)
        self.connect(sb_from, sb_to)

    def realize(self):
        # create muxs
        result = {}
        for coord in self.graph_:
            tile = self.graph_[coord]
            sbs_mux = []
            cb_mux = []

            sbs = tile.switchbox.get_all_sbs()
            for sb in sbs:
                mux = sb.mux_block.create_mux()
                sbs_mux.append(mux)
            for _, port in tile.ports.items():
                mux = port.mux_block.create_mux()
                cb_mux.append(mux)
            # registers don't need a mux
            result[coord] = *sbs_mux, *cb_mux
        return result

    @staticmethod
    def compute_num_tracks(x_offset: int, y_offset: int,
                           x: int, y: int, track_info: Dict[int, int]):
        """compute the num of tracks needed for (x, y), given the track
        info"""
        x_diff = x - x_offset
        y_diff = y - y_offset
        result = 0
        for length, num_track in track_info:
            if x_diff % length == 0 and y_diff % length == 0:
                # it's the tile
                result += num_track
        return result

    def name(self):
        return f"Interconnect {self.track_width}"


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
                                sb_type: SwitchBoxType) -> Interconnect:
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
    interconnect = Interconnect(track_width, InterconnectType.Mesh)
    # create tiles and set cores
    for x in range(x_offset, width - x_offset):
        for y in range(y_offset, height - y_offset, tile_height):
            # compute the number of tracks
            num_track = interconnect.compute_num_tracks(x_offset, y_offset,
                                                        x, y, track_info)
            # create switch based on the type passed in
            if sb_type == SwitchBoxType.Disjoint:
                switch_wires = SwitchBoxHelper.get_disjoint_sb_wires(num_track)
            elif sb_type == SwitchBoxType.Wilton:
                switch_wires = SwitchBoxHelper.get_wilton_sb_wires(num_track)
            elif sb_type == SwitchBoxType.Imran:
                switch_wires = SwitchBoxHelper.get_imran_sb_wires(num_track)
            else:
                raise NotImplementedError(sb_type)
            switch = Switch(x, y, num_track, width, switch_wires)
            tile = Tile(x, y, width, switch, height=tile_height)
            interconnect.add_tile(tile)
            interconnect.set_core(x, y, column_core_fn(x, y))
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
            interconnect.connect_switch(x_offset, y_offset, width, height,
                                        track_len,
                                        current_track,
                                        InterconnectPolicy.Ignore)
            current_track += 1

    # realize the sbs, cbs
    interconnect.realize()

    return interconnect
