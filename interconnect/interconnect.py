"""
This module is a more user-friendly Python wrapper for the Cyclone routing
engine. The main idea is that when the user is assembling the basic circuit
together using generators, the system automatically creates a routing graph.

Some of the wrapping is due to naming convention. For instance, in Cyclone,
switch box sides are identified as top/bottom/right/left, which is consistent
with other popular routers. In Garnet we use north/source/east/west, hence a
conversion is needed.

This module mainly deal with the actual
"""
import enum
import pycyclone
import generator.generator as generator
from typing import Union, Tuple

GridCoordinate = Tuple[int, int]


# helper class to create complex switch  design
class SwitchManager:
    """A class to manage different types of switch boxes. It is designed to
    handle assigning the recognizing switch IDs. It is because cyclone
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


class InterconnectType(enum.Enum):
    Mesh = 0
    Hierarchical = 1
    Hybrid = 2


class Switch(generator.Generator):
    def __init__(self, switchbox: pycyclone.Switch):
        super().__init__()
        self.switchbox_ = switchbox

    def name(self):
        return ""


class Tile(generator.Generator):
    def __init__(self, x: int, y: int, height: int, switch: Switch):
        super().__init__()
        self.tile_ = pycyclone.Tile(x, y, height, switch.switchbox_)
        self.x = x
        self.y = y
        if height < 1:
            raise RuntimeError(f"height has to be at least 1, got {height}")
        self.height = height
        self.switch = switch

    def name(self):
        return self.tile_.to_string()


class Interconnect(generator.Generator):
    def __init__(self, connection_type: InterconnectType):
        super().__init__()
        if connection_type != InterconnectType.Mesh:
            raise NotImplemented("Only Mesh network is currently supported")
        self.graph_ = pycyclone.RoutingGraph()

        # this is a 2d grid consistent with the routing graph. it's designed
        # to support fast query with irregular tile height.
        self.grid_ = []

    def add_tile(self, tile: Tile) -> None:
        self.graph_.add_tile(tile.tile_)
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
                tile_name = self.grid_[tile_index[0]][tile_index[1]].name()
            raise RuntimeError(f"Tile ({x}, {y}) is assigned with " +
                               tile_name)

    def get_size(self) -> Tuple[int, int]:
        height = len(self.grid_)
        width = len(self.grid_[0])
        return width, height

    def name(self):
        return "Interconnect"
