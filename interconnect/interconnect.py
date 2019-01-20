import enum
import abc
import generator.generator as generator
from common.core import Core
from typing import Union, Tuple, List, Dict
from .cyclone import SwitchBoxSide, SwitchBoxIO, InterconnectGraph, Tile as GTile
from .circuit import Connectable
from .tile_circuit import TileCircuit, SBConnectionType

GridCoordinate = Tuple[int, int]


class InterconnectType(enum.Enum):
    Mesh = 0
    Hierarchical = 1
    Hybrid = 2





class Interconnect(InterConnectABC):
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
        super().__init__(track_width, connection_type)

        if connection_type != InterconnectType.Mesh:
            raise NotImplementedError("Only Mesh network is currently "
                                      "supported")
        self.__graph = InterconnectGraph()

        # this is a 2d grid consistent with the routing graph. it's designed
        # to support fast query with irregular tile height.
        self.__tile_grid: List[List[Union[TileCircuit, None]]] = []

    def add_tile(self, tile: Union[TileCircuit, GTile]) -> None:
        if isinstance(tile, GTile):
            tile = TileCircuit(tile)
        self.__graph.add_tile(tile.g_tile)


    def connect(self, circuit_from: Connectable, circuit_to: Connectable):
        # making sure that node to and from are indeed from the
        # interconnect circuit
        assert circuit_from in self
        assert circuit_to in self
        circuit_from.connect(circuit_to)

    def disconnect(self, circuit_from: Connectable, circuit_to: Connectable):
        assert circuit_from in self
        assert circuit_to in self
        circuit_from.disconnect(circuit_to)

    def is_connected(self, circuit_from: Connectable,
                     circuit_to: Connectable):
        if circuit_from not in self or circuit_to not in self:
            return False
        return circuit_from.is_connected(circuit_to)




    def realize(self):
        # create muxs
        result = {}
        visited = set()
        width, height = self.get_size()
        for y in range(height):
            for x in range(width):
                tile = self.get_tile(x, y)
                if tile is not None and (tile.x, tile.y) not in visited:
                    result[(tile.x, tile.y)] = tile.realize()

                    visited.add((tile.x, tile.y))
        return result

    def add_config_reg(self, addr_width, data_width):
        visited = set()
        width, height = self.get_size()
        for y in range(height):
            for x in range(width):
                tile = self.get_tile(x, y)
                if tile is not None and (tile.x, tile.y) not in visited:
                    tile.add_config_reg(addr_width, data_width)
                    visited.add((tile.x, tile.y))


    def name(self):
        return f"Interconnect {self.track_width}"
