"""
This module is a more user-friendly Python wrapper for the Cyclone routing
engine. The main idea is that when the user is assembling the basic circuit
together using generators, the system automatically creates a routing graph.
It will also construct proper magma circuit based on the Cyclone interconnect
graph.

Some of the wrapping is due to naming convention. For instance, in Cyclone,
switch box sides are identified as top/bottom/right/left, which is consistent
with other popular routers. In Garnet we use north/source/east/west, hence a
conversion is needed.

Cyclone is design to be generic and able to handle any kinds of interconnect.
I (Keyi) will try my best to preserve the same level of flexibility whenever
possible.

"""
import enum
import pycyclone
import generator.generator as generator
from common.core import Core
from typing import Union, Tuple, NamedTuple, List

GridCoordinate = Tuple[int, int]


# helper class to create complex switch  design
class SwitchManager:
    """A class to manage different types of switch boxes. It is designed to
    handle assigning and recognizing switch IDs. It is because cyclone
    specifies it's the user's responsibility to ensure the uniqueness of
    different switch internal wirings
    """
    def __init__(self):
        self.id_count = 0
        self.sb_wires = {}

    def create_disjoint_switch(self, x: int, y: int, bit_width: int,
                               num_tracks: int) -> pycyclone.Switch:
        internal_connections = pycyclone.util.get_disjoint_sb_wires(num_tracks)
        switch_id = self.get_switch_id(internal_connections)
        return pycyclone.Switch(x, y, num_tracks, bit_width, switch_id,
                                internal_connections)

    def get_switch_id(self, internal_connections) -> int:
        for switch_id in self.sb_wires:
            wires = self.sb_wires[switch_id]
            if len(wires) != len(internal_connections):
                # not the same
                continue
            for pair in wires:
                if pair not in internal_connections:
                    # doesn't have that connection
                    continue
            return switch_id
        switch_id = self.id_count
        self.sb_wires[switch_id] = internal_connections
        self.id_count += 1
        return switch_id


class SwitchBoxSide(enum.Enum):
    """Rename the sides"""
    NORTH = pycyclone.SwitchBoxSide.Top
    SOUTH = pycyclone.SwitchBoxSide.Bottom
    EAST = pycyclone.SwitchBoxSide.Right
    WEST = pycyclone.SwitchBoxSide.Left


class SwitchBoxIO(enum.Enum):
    """hides underlying cyclone implementation"""
    IN = pycyclone.SwitchBoxIO.SB_IN
    OUT = pycyclone.SwitchBoxIO.SB_OUT


class InterconnectType(enum.Enum):
    Mesh = 0
    Hierarchical = 1
    Hybrid = 2


# garnet's PEP 8 doesn't like the new way to declare named tuple with type hints
# using the old format
SBConnectionType = NamedTuple("SBConnectionType",
                              [("side", SwitchBoxSide),
                               ("track", int),
                               ("io", SwitchBoxIO)])


class Switch(generator.Generator):
    def __init__(self, switchbox: pycyclone.Switch):
        super().__init__()
        self.switchbox_ = switchbox
        self.x = switchbox.x
        self.y = switchbox.y

    def __getitem__(self, value: Tuple[SwitchBoxSide, int,
                                       pycyclone.SwitchBoxIO]):
        side, track, io = value
        side = side.value
        io = io.value
        return self.switchbox_[side, track, io]

    def name(self):
        return self.switchbox_.to_string()


class Tile(generator.Generator):
    def __init__(self, x: int, y: int, height: int):
        super().__init__()
        self.x = x
        self.y = y
        if height < 1:
            raise RuntimeError(f"height has to be at least 1, got {height}")
        self.height = height
        # we don't set core in the constructor because some tiles may not have
        # core, e.g. IO tiles. Or if we want to create a by-pass tile without
        # core functionality, such as the bottom half of a tall MEM tile
        self.core = None

    def set_core(self, core: Core):
        self.core = core

    def core_has_input(self, port: str):
        if self.core is None:
            return False
        for pr in self.core.inputs():
            if pr.qualified_name() == port:
                return True
        return False

    def core_has_output(self, port: str):
        if self.core is None:
            return False
        for pr in self.core.outputs():
            if pr.qualified_name() == port:
                return True
        return False

    def name(self):
        return f"Tile ({self.x}, {self.y}, {self.height})"


class Interconnect(generator.Generator):
    def __init__(self, track_width: int, connection_type: InterconnectType):
        super().__init__()
        self.track_width = track_width
        if connection_type != InterconnectType.Mesh:
            raise NotImplementedError("Only Mesh network is currently "
                                      "supported")
        self.graph_ = pycyclone.RoutingGraph()

        # this is a 2d grid consistent with the routing graph. it's designed
        # to support fast query with irregular tile height.
        self.grid_ = []

    def add_tile(self, tile: Tile, switch: Switch) -> None:
        t = pycyclone.Tile(tile.x, tile.y, tile.height, switch.switchbox_)
        self.graph_.add_tile(t)
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

    def get_cyclone_tile(self, x: int, y: int) -> pycyclone.Tile:
        t = self.get_tile(x, y)
        tile = self.graph_[t.x, t.y]
        return tile

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

    def set_core_connection_in(self, x: int, y: int, port_name: str,
                               connection_type: List[SBConnectionType]):
        # we add a new port here
        tile = self.get_tile(x, y)
        # make sure that it's an input port
        if not tile.core_has_input(port_name):
            raise RuntimeError(port_name + " not in the core " +
                               tile.core.name())
        port_node = pycyclone.PortNode(port_name, tile.x, tile.y,
                                       self.track_width)
        # add to graph node first, we will handle magma in a different pass
        # based on the graph, since we need to compute the mux height
        for side, track, io in connection_type:
            sb = pycyclone.SwitchBoxNode(tile.x, tile.y, self.track_width,
                                         track, side.value, io.value)
            self.graph_.add_edge(sb, port_node)

    def set_core_connection_out(self, x: int, y: int, port_name: str,
                                connection_type: List[SBConnectionType]):
        # we add a new port here
        tile = self.get_tile(x, y)
        port_node = pycyclone.PortNode(port_name, tile.x, tile.y,
                                       self.track_width)
        # make sure that it's an input port
        if not tile.core_has_output(port_name):
            raise RuntimeError(port_name + " not in the core " +
                               tile.core.name())
        # add to graph node first, we will handle magma in a different pass
        # based on the graph, since we need to compute the mux height
        for side, track, io in connection_type:
            sb = pycyclone.SwitchBoxNode(tile.x, tile.y, self.track_width,
                                         track, side.value, io.value)
            self.graph_.add_edge(port_node, sb)

    # wrapper function for the underlying cyclone graph
    def get_sb(self, x: int, y: int, side: SwitchBoxSide, track: int,
               io: SwitchBoxIO):
        return self.graph_.get_sb(x, y, side.value, track, io.value)

    def get_port(self, x: int, y: int, port_name: str):
        return self.graph_.get_port(x, y, port_name)

    def name(self):
        return f"Interconnect {self.track_width}"
