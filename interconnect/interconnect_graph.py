# NOTE(rsetaluri): This import is needed to allow classes to refer to themselves
# in type annotations. See: https://www.python.org/dev/peps/pep-0563/.
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
import enum
from ordered_set import OrderedSet


@enum.unique
class Side(enum.Enum):
    """
    We use the same mapping from cyclone for convenience:

       3
      ---
    2 | | 0
      ---
       1
    """
    NORTH = 3
    SOUTH = 1
    EAST = 0
    WEST = 2


@enum.unique
class IODirection(enum.Enum):
    IN = 0
    OUT = 1


@dataclass(unsafe_hash=True)
class Node(ABC):
    width: int

    def __post_init__(self):
        self.neighbors = OrderedSet()
        self.incoming = []
        self.edge_cost = {}

    def add_edge(self, node: Node, delay: int = 0):
        assert self.width == node.width
        self.neighbors.add(node)
        node.incoming.append(self)
        self.edge_cost[node] = delay

    def remove_edge(self, node: Node):
        if node not in self.neighbors:
            return
        self.edge_cost.pop(node)
        self.neighbors.remove(node)
        # Remove the incoming connections on @node as well.
        node.incoming.remove(self)

    def get_edge_cost(self, node: Node) -> int:
        if node not in self.edge_cost:
            return self.MAX_DEFAULT_DELAY
        return self.edge_cost[node]

    def get_incoming(self):
        return self.incoming

    def __iter__(self):
        return iter(self.neighbors)

    def __len__(self):
        return len(self.neighbors)


@dataclass(unsafe_hash=True)
class Port(Node):
    name: str


@dataclass(unsafe_hash=True)
class Register(Node):
    name: str
    track: int


@dataclass(unsafe_hash=True)
class SwitchNode(Node):
    track: int
    side: Side
    io: IODirection


@dataclass
class SwitchBox:
    width: int
    num_tracks: int
    connections: List[Tuple[int, Side, int, Side]]

    def __post_init__(self):
        self.nodes = {}
        # Initialize SwitchNode objects.
        for side in Side:
            for io in IODirection:
                for track in range(self.num_tracks):
                    node = SwitchNode(self.width, track, side, io)
                    self.nodes[(side, io, track)] = node
        # Construct (internal) connections.
        for (t0, s0, t1, s1) in self.connections:
            src_node = self.nodes[(s0, IODirection.IN, t0)]
            dst_node = self.nodes[(s1, IODirection.OUT, t1)]
            # We assume that connections internal to the SwitchBox have zero
            # delay.
            src_node.add_edge(dst_node, 0)

    def __eq__(self, other: SwitchBox) -> bool:
        if not isinstance(other, SwitchBox):
            return False
        if len(self.connections) != len(other.connections):
            return False
        # TODO(rsetaluri): Accelerate this computation.
        for conn in self.connections:
            if conn not in other.connections:
                return False
        return True


class CoreInterface(ABC):
    @abstractmethod
    def inputs(self) -> List[Port]:
        pass

    @abstractmethod
    def outputs(self) -> List[Port]:
        pass


@dataclass
class Tile:
    bit_width: int
    switch_box: SwitchBox
    height: int = 1

    def __post_init__(self):
        self.core = None
        self.registers = {}

    def set_core(self, core: CoreInterface):
        self.core = core        


class InterconnectGraph:
    def __init__(self):
        self.mesh = {}  # Dict[Tuple[int, int], Tile]

    def set_tile(self, x: int, y: int, tile: Tile):
        # TODO(rsetaluri): Check if (x, y) already occupied.
        self.mesh[(x, y)] = tile

    def unset_tile(self, x: int, y: int):
        if (x, y) in self.mesh:
            del self.mesh[(x, y)]

    def get_tile(self, x: int, y: int) -> Tile:
        if (x, y) not in self.mesh:
            raise KeyError(f"({x}, {y}) not set")
        return self.mesh[(x, y)]

    def serialize(self, filename: str):
        # TODO(rsetaluri): Implement this.
        pass
