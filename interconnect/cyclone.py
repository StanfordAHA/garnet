"""
This implementation is converted from
https://github.com/Kuree/cgra_pnr/blob/master/cyclone/src/graph.hh
with adjustments due to language difference.

"""
import enum
from typing import List, Tuple, Dict, Set
from abc import ABC, abstractmethod
import magma


@enum.unique
class NodeType(enum.Enum):
    SwitchBox = enum.auto()
    Port = enum.auto()
    Register = enum.auto()
    Generic = enum.auto()


@enum.unique
class SwitchBoxSide(enum.Enum):
    """
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

    def __repr__(self):
        side = self
        if side == SwitchBoxSide.NORTH:
            return "north"
        elif side == SwitchBoxSide.SOUTH:
            return "south"
        elif side == SwitchBoxSide.EAST:
            return "east"
        elif side == SwitchBoxSide.WEST:
            return "west"
        else:
            raise ValueError("unknown value", side)

    def get_opposite_side(self) -> "SwitchBoxSide":
        side = self
        if side == SwitchBoxSide.NORTH:
            return SwitchBoxSide.SOUTH
        elif side == SwitchBoxSide.SOUTH:
            return SwitchBoxSide.NORTH
        elif side == SwitchBoxSide.EAST:
            return SwitchBoxSide.WEST
        elif side == SwitchBoxSide.WEST:
            return SwitchBoxSide.EAST
        else:
            raise ValueError("unknown value", side)


class SwitchBoxIO(enum.Enum):
    SB_IN = 0
    SB_OUT = 1


class NodeABC(ABC):
    TOKEN = "NODE"

    def __init__(self, x: int, y: int, width: int):
        self.x = x
        self.y = y
        self.width = width

        # holds circuit
        self.circuit = None

    @abstractmethod
    def __repr__(self):
        return ""

    @abstractmethod
    def __eq__(self, other):
        pass

    @abstractmethod
    def __iter__(self):
        pass

    @abstractmethod
    def add_edge(self, node: "NodeABC", delay: int = 0):
        pass

    def get_conn_in(self) -> List["NodeABC"]:
        pass


class Node(NodeABC):
    MAX_DEFAULT_DELAY = 100000

    def __init__(self, name: str, node_type: NodeType, x: int, y: int,
                 track: int, width: int):
        super().__init__(x, y, width)
        self.name = name
        self.type = node_type
        self.track = track

        self.__neighbors = []
        self.__conn_ins = []
        self.__edge_cost = dict()

    def add_edge(self, node: "Node", delay: int = 0):
        # basically we want an ordered set, which is implemented as a list
        if node not in self.__neighbors:
            self.__neighbors.append(node)
            node.__conn_ins.append(self)
            self.__edge_cost[node] = delay

    @abstractmethod
    def __hash__(self):
        pass

    def _default_hash(self):
        return self.name.__hash__() ^ self.type.__hash__() ^ \
               self.x.__hash__() ^ self.y.__hash__() ^ \
               self.width.__hash__() ^ self.track.__hash__()

    def get_edge_cost(self, node: "Node") -> int:
        if node not in self.__edge_cost:
            return self.MAX_DEFAULT_DELAY
        else:
            return self.__edge_cost[node]

    def get_conn_in(self):
        return self.__conn_ins

    def __eq__(self, other):
        if not isinstance(other, Node):
            return False
        if not self.type == other.type:
            return False

        # only compares x, y, and width
        return self.x == other.x and self.y == other.y and \
            self.width == other.width

    def __iter__(self):
        return iter(self.__neighbors)


class PortNode(Node):
    TOKEN = "PORT"

    def __init__(self, name: str, x: int, y: int, width: int):
        super().__init__(name, NodeType.Port, x, y, 0, width)

    def __repr__(self):
        return f"{self.TOKEN} {self.name} ({self.x}, {self.y}, {self.width})"

    def __eq__(self, other):
        if not super(Node).__eq__(other):
            return False
        return self.name == other.name

    def __hash__(self):
        return super()._default_hash()


class RegisterNode(Node):
    TOKEN = "REG"

    def __init__(self, name: str, x: int, y: int, track: int, width: int):
        super().__init__(name, NodeType.Port, x, y, track, width)

    def __repr__(self):
        return f"{self.TOKEN} {self.name} ({self.track}, {self.x},"\
            f" {self.y}, {self.width})"

    def __eq__(self, other):
        if not super(Node).__eq__(other):
            return False
        return self.track == other.track and self.name == other.name

    def __hash__(self):
        return super()._default_hash()


class SwitchBoxNode(Node):
    TOKEN = "SB"

    def __init__(self, x: int, y: int, track: int, width: int,
                 side: SwitchBoxSide, io: SwitchBoxIO):
        super().__init__("", NodeType.SwitchBox, x, y, track, width)
        self.side = side
        self.io = io

    def __repr__(self):
        return f"{self.TOKEN} ({self.track}, {self.x}, {self.y}, " + \
               f"{self.side.value}, {self.io.value})"

    def __eq__(self, other):
        if not super(Node).__eq__(other):
            return False
        return self.track == other.track and self.side == other.side and \
            self.io == other.io

    def __hash__(self):
        return super()._default_hash() ^ self.side.__hash__() \
               ^ self.io.__hash__()


class Switch:
    TOKEN = "SWITCH"
    NUM_SIDES = 4
    NUM_IOS = 2

    def __init__(self, x: int, y: int, num_track: int, width: int,
                 internal_wires: List[Tuple[int, SwitchBoxSide,
                                            int, SwitchBoxSide]]):
        self.x = x
        self.y = y
        self.width = width

        self.__sbs: List[List[List[SwitchBoxNode]]] = [[[None] * num_track] *
                                                       self.NUM_IOS] * \
            self.NUM_SIDES

        self.num_track = num_track
        # construct the internal connections
        for side in range(self.NUM_SIDES):
            for io in range(self.NUM_IOS):
                for track in range(num_track):
                    node = SwitchBoxNode(x, y, track, width,
                                         SwitchBoxSide(side),
                                         SwitchBoxIO(io))
                    self.__sbs[side][io][track] = node

        # assign internal wiring
        # the order is in -> out
        for conn in internal_wires:
            track_from, side_from, track_to, side_to = conn
            sb_from = \
                self.__sbs[side_from.value][SwitchBoxIO.SB_IN.value][track_from]
            sb_to = \
                self.__sbs[side_to.value][SwitchBoxIO.SB_OUT.value][track_to]
            # internal sb connection has no delay
            sb_from.add_edge(sb_to, 0)

        self.internal_wires = internal_wires

        # used to identify different types of switches
        self.id = 0

    def __eq__(self, other):
        if not isinstance(other, Switch):
            return False
        if len(self.internal_wires) != other.internal_wires:
            return False
        # check bijection
        for conn in self.internal_wires:
            if conn not in other.internal_wires:
                return False
        return True

    def __repr__(self):
        return f"{self.TOKEN} {self.width} {self.id} {self.num_track}"

    def __getitem__(self, item: Tuple[SwitchBoxSide, int, SwitchBoxIO]):
        if not isinstance(item, tuple):
            raise ValueError("index has to be a tuple")
        if len(item) != 3:
            raise ValueError("index has to be length 3")
        if not isinstance(item[0], SwitchBoxSide):
            raise ValueError(item[0])
        if not isinstance(item[-1], SwitchBoxIO):
            raise ValueError(item[-1])
        side, track, io = item
        return self.__sbs[side.value][io.value][track]

    def get_all_sbs(self) -> List[SwitchBoxNode]:
        result = []
        for track in range(self.num_track):
            for side in range(self.NUM_SIDES):
                for io in range(self.NUM_IOS):
                    result.append(self.__sbs[side][io][track])
        return result


class Tile:
    TOKEN = "TILE"

    def __init__(self, x: int, y: int, track_width: int, switchbox: Switch,
                 height: int = 1):
        self.x = x
        self.y = y
        self.track_width = track_width
        self.height = height

        # create a copy of switch box because the switchbox nodes have to be
        # created
        self.switchbox: Switch = Switch(x, y, switchbox.num_track,
                                        switchbox.width,
                                        switchbox.internal_wires)

        self.ports: Dict[str, PortNode] = {}
        self.registers: Dict[str, RegisterNode] = {}

        self.inputs: Set = set()
        self.outputs: Set = set()

    def __eq__(self, other):
        if not isinstance(other, Tile):
            return False
        return self.x == other.x and self.y == other.y and \
            self.height == other.height

    def __repr__(self):
        return f"{self.TOKEN} ({self.x}, {self.y}, {self.height}, " +\
               f"{self.switchbox.id})"

    def set_core(self, core):
        self.inputs = set()
        self.outputs = set()

        for port in core.inputs():
            port_name = port.qualified_name()
            width = self.__get_bit_width(port)
            if width == self.track_width:
                self.inputs.add(port_name)
                # create node
                self.ports[port_name] = PortNode(port_name, self.x, self.y,
                                                 self.track_width)
        for port in core.outputs():
            port_name = port.qualified_name()
            width = self.__get_bit_width(port)
            if width == self.track_width:
                self.outputs.add(port_name)
                # create node
                self.ports[port_name] = PortNode(port_name, self.x, self.y,
                                                 self.track_width)

    @staticmethod
    def __get_bit_width(port):
        # nasty function to get the actual bitwidth from the port reference
        t = port.type()
        if isinstance(t, magma.BitKind):
            return 1
        if isinstance(port.type(), magma.BitsKind):
            return len(t)
        raise NotImplementedError(t, type(t))

    def core_has_input(self, port: str):
        return port in self.inputs

    def core_has_output(self, port: str):
        return port in self.outputs

    def name(self):
        return str(self)

    @staticmethod
    def create_tile(x: int, y: int, num_tracks: int, bit_width: int,
                    internal_wires: List[Tuple[int, SwitchBoxSide,
                                               int, SwitchBoxSide]],
                    height: int = 1):
        switch = Switch(x, y, num_tracks, bit_width, internal_wires)
        tile = Tile(x, y, bit_width, switch, height)
        return tile


class Graph:
    def __init__(self):
        self.__grid: Dict[Tuple[int, int], Tile] = {}
        self.__switch_ids: Dict[int, Switch] = {}

    def add_tile(self, tile: Tile):
        tile.switchbox.id = self.__assign_id(tile.switchbox)
        self.__grid[(tile.x, tile.y)] = tile

    def __assign_id(self, switch: Switch) -> int:
        for switch_id, s in self.__switch_ids.items():
            if switch == s:
                return switch_id
        switch_id = len(self.__switch_ids)
        self.__switch_ids[switch_id] = switch
        return switch_id

    def remove_tile(self, coord: Tuple[int, int]):
        if coord in self.__grid:
            self.__grid.pop(coord)

    def add_edge(self, node_from: Node, node_to: Node, wire_delay: int = 1):
        n1 = self.__search_create_node(node_from)
        n2 = self.__search_create_node(node_to)

        if n1.width != n2.width:
            raise ValueError(f"{n1.width} != {n2.width}")

        n1.add_edge(n2, wire_delay)

    def __search_create_node(self, node) -> Node:
        # nodes are owned and managed by graph
        # internal nodes are created based on the external node
        x, y = node.x, node.y
        tile = self.__grid[(x, y)]
        if isinstance(node, RegisterNode):
            if node.name not in tile.registers:
                tile.registers[node.name] = RegisterNode(node.name, node.x,
                                                         node.y, node.track,
                                                         node.width)
            return tile.registers[node.name]
        elif isinstance(node, PortNode):
            if node.name not in tile.ports:
                tile.ports[node.name] = PortNode(node.name, node.x, node.y,
                                                 node.width)
            return tile.ports[node.name]
        elif isinstance(node, SwitchBoxNode):
            if node.track >= tile.switchbox.num_track:
                raise IndexError(node.track, tile.switchbox.num_track)
            return tile.switchbox[node.side, node.track, node.io]
        else:
            raise TypeError(node, Node.__name__)

    def coords(self):
        return self.__grid.keys()

    def __getitem__(self, item: Tuple[int, int]):
        return self.__grid[item]

    def dump_graph(self, filename: str):
        with open(filename, "w+") as f:
            padding = "  "
            begin = "BEGIN"
            end = "END"

            def write_line(value):
                f.write(value + "\n")

            def write_conn(node_):
                # TODO: need to test if it is deterministic
                write_line(str(node_))
                write_line(begin)
                for n in node_:
                    write_line(padding * 3 + str(n))
                write_line(end)

            for _, switch in self.__switch_ids.items():
                write_line(str(switch))
                write_line(begin)
                for conn in switch.internal_wires:
                    track_from, side_from, track_to, side_to = conn
                    write_line(padding + " ".join([str(track_from),
                                                  str(side_from.value),
                                                  str(track_to),
                                                  str(side_to.value)]))
                write_line(end)
            for _, tile in self.__grid.items():
                write_line(str(tile))
                write_line(begin)
                sbs = tile.switchbox.get_all_sbs()
                for sb in sbs:
                    write_conn(sb)
                for node in tile.ports:
                    write_conn(node)
                for reg in tile.registers:
                    write_conn(reg)
                write_line(end)
