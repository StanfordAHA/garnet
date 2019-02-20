"""
This implementation is converted from
https://github.com/Kuree/cgra_pnr/blob/master/cyclone/src/graph.hh
with adjustments due to language difference.

"""
import enum
from typing import List, Tuple, Dict, Union, NamedTuple, Iterator
from ordered_set import OrderedSet
from abc import abstractmethod


MAX_DEFAULT_DELAY = 100000


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


class SBConnectionType(NamedTuple):
    side: SwitchBoxSide
    track: int
    io: SwitchBoxIO


class InterconnectPolicy(enum.Enum):
    PassThrough = enum.auto()
    Ignore = enum.auto()


class InterconnectCore:
    @abstractmethod
    def inputs(self) -> List[Tuple[int, str]]:
        pass

    @abstractmethod
    def outputs(self) -> List[Tuple[int, str]]:
        pass

    @abstractmethod
    def get_port_ref(self, port_name: str):
        pass

    @abstractmethod
    def __eq__(self, other):
        pass


class Node:
    def __init__(self, x: int, y: int, width: int):
        self.x = x
        self.y = y
        self.width = width

        self.__neighbors = OrderedSet()
        self.__conn_ins = []
        self.__edge_cost = {}

    def add_edge(self, node: "Node", delay: int = 0):
        assert self.width == node.width
        if node not in self.__neighbors:
            self.__neighbors.add(node)
            node.__conn_ins.append(self)
            self.__edge_cost[node] = delay

    def remove_edge(self, node: "Node"):
        if node in self.__neighbors:
            self.__edge_cost.pop(node)
            self.__neighbors.remove(node)

            # remove the incoming connections as well
            node.__conn_ins.remove(self)

    def get_edge_cost(self, node: "Node") -> int:
        if node not in self.__edge_cost:
            return MAX_DEFAULT_DELAY
        else:
            return self.__edge_cost[node]

    def get_conn_in(self) -> List["Node"]:
        return self.__conn_ins

    def __iter__(self) -> Iterator["Node"]:
        return iter(self.__neighbors)

    def __len__(self):
        return len(self.__neighbors)

    @abstractmethod
    def __repr__(self):
        pass

    @abstractmethod
    def node_str(self):
        pass

    def __contains__(self, item):
        return item in self.__neighbors

    def __hash__(self):
        return hash(self.width) ^ hash(self.x) ^ hash(self.y)


class PortNode(Node):
    def __init__(self, name: str, x: int, y: int, width: int):
        super().__init__(x, y, width)

        self.name: str = name

    def node_str(self):
        return f"PORT {self.name} ({self.x}, {self.y}, {self.width})"

    def __repr__(self):
        return f"CB_{self.name}"

    def __hash__(self):
        return super().__hash__() ^ hash(self.name)


class RegisterNode(Node):
    def __init__(self, name: str, x: int, y: int, track: int, width: int):
        super().__init__(x, y, width)

        self.name: str = name
        self.track: int = track

    def node_str(self):
        return f"REG {self.name} ({self.track}, {self.x},"\
            f" {self.y}, {self.width})"

    def __repr__(self):
        return f"REG_{self.name}_B{self.width}"

    def __hash__(self):
        return super().__hash__() ^ hash(self.name) ^ hash(self.track)


class SwitchBoxNode(Node):
    def __init__(self, x: int, y: int, track: int, width: int,
                 side: SwitchBoxSide, io: SwitchBoxIO):
        super().__init__(x, y, width)

        self.track = track
        self.side = side
        self.io = io

    def node_str(self):
        return f"SB ({self.track}, {self.x}, {self.y}, " + \
               f"{self.side.value}, {self.io.value}, {self.width})"

    def __repr__(self):
        return f"SB_T{self.track}_{self.side.name}_{self.io.name}_B{self.width}"

    def __hash__(self):
        return super().__hash__() ^ hash(self.track) ^ hash(self.side) ^ \
            hash(self.io)


class RegisterMuxNode(Node):
    def __init__(self, x: int, y: int, track: int, width: int,
                 side: SwitchBoxSide):
        super().__init__(x, y, width)

        self.track = track
        self.side = side

        self.name = f"{self.side}_{self.track}"

    def node_str(self):
        return f"RMUX ({self.track}, {self.x}, {self.y}, " +\
               f"{self.side.value}, {self.width})"

    def __repr__(self):
        return f"RMUX_T{self.track}_{self.side.name}_B{self.width}"

    def __hash__(self):
        return super().__hash__() ^ hash(self.track) ^ hash(self.side)


class SwitchBox:
    def __init__(self, x: int, y: int, num_track: int, width: int,
                 internal_wires: List[Tuple[int, SwitchBoxSide,
                                            int, SwitchBoxSide]]):
        self.x = x
        self.y = y
        self.width = width

        self.num_track = num_track
        self.internal_wires = internal_wires

        self.id = 0

        self.__sbs: List[List[List[SwitchBoxNode]]] = \
            [[[None for _ in range(self.num_track)]
              for _ in SwitchBoxIO] for _ in SwitchBoxSide]

        # construct the internal connections
        for side in SwitchBoxSide:
            for io in SwitchBoxIO:
                for track in range(self.num_track):
                    node = SwitchBoxNode(self.x, self.y, track, width,
                                         side, io)
                    self.__sbs[side.value][io.value][track] = node

        # assign internal wiring
        # the order is in -> out
        for conn in self.internal_wires:
            track_from, side_from, track_to, side_to = conn
            sb_from = \
                self.__sbs[side_from.value][SwitchBoxIO.SB_IN.value][track_from]
            sb_to = \
                self.__sbs[side_to.value][SwitchBoxIO.SB_OUT.value][track_to]
            # internal sb connection has no delay
            sb_from.add_edge(sb_to, 0)

        # used to identify different types of switches
        self.id = 0

        # hold the pipeline register related nodes
        self.registers: Dict[str, RegisterNode] = {}
        self.reg_muxs: Dict[str, RegisterMuxNode] = {}

    def __eq__(self, other):
        if not isinstance(other, SwitchBox):
            return False
        if len(self.internal_wires) != len(other.internal_wires):
            return False
        # check bijection
        for conn in self.internal_wires:
            if conn not in other.internal_wires:
                return False
        return True

    def __repr__(self):
        return f"SWITCH {self.width} {self.id} {self.num_track}"

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
            for side in SwitchBoxSide:
                for io in SwitchBoxIO:
                    sb = self.get_sb(side, track, io)
                    if sb is not None:
                        result.append(sb)
        return result

    def get_sb(self, side: SwitchBoxSide,
               track: int,
               io: SwitchBoxIO) -> Union[SwitchBoxNode, None]:
        # we may have removed the nodes
        if track < len(self.__sbs[side.value][io.value]):
            return self.__sbs[side.value][io.value][track]
        else:
            return None

    def remove_side_sbs(self, side: SwitchBoxSide, io: SwitchBoxIO):
        # first remove the connections and nodes
        for sb in self.__sbs[side.value][io.value]:
            # create a snapshot before removes them
            nodes_to_remove = list(sb)
            for node in nodes_to_remove:
                sb.remove_edge(node)
            for node in sb.get_conn_in():
                node.remove_edge(sb)

        self.__sbs[side.value][io.value].clear()
        # then remove the internal wires
        wires_to_remove = set()
        for conn in self.internal_wires:
            _, side_from, _, side_to = conn
            if io == SwitchBoxIO.SB_IN and side_from == side:
                wires_to_remove.add(conn)
            elif io == SwitchBoxIO.SB_OUT and side_to == side:
                wires_to_remove.add(conn)
        for conn in wires_to_remove:
            self.internal_wires.remove(conn)

    def add_pipeline_register(self, side: SwitchBoxSide, track: int):
        # find that specific sb node
        node = self.get_sb(side, track, SwitchBoxIO.SB_OUT)
        if node is None:
            return
        neighbors = {}
        for n in node:
            if isinstance(n, RegisterNode) or isinstance(n, RegisterMuxNode):
                raise Exception("pipeline register already inserted")
            cost = node.get_edge_cost(n)
            neighbors[n] = cost
        # disconnect them first
        for n in neighbors:
            node.remove_edge(n)
        # create a register mux node and a register node
        reg = RegisterNode(f"T{track}_{side.name}", node.x, node.y, track,
                           node.width)
        reg_mux = RegisterMuxNode(node.x, node.y, track, node.width,
                                  side)
        # connect node to them
        node.add_edge(reg)
        node.add_edge(reg_mux)
        # connect reg to the reg_mux
        reg.add_edge(reg_mux)

        # add the connect back from the neighbors
        for n, cost in neighbors.items():
            reg_mux.add_edge(n, cost)

        # last step: add to the tile level
        assert reg.name not in self.registers
        assert reg_mux.name not in self.reg_muxs
        self.registers[reg.name] = reg
        self.reg_muxs[reg_mux.name] = reg_mux


# helper class
class DisjointSwitchBox(SwitchBox):
    def __init__(self, x: int, y: int, num_track: int, width: int):
        internal_wires = SwitchBoxHelper.get_disjoint_sb_wires(num_track)
        super().__init__(x, y, num_track, width, internal_wires)


class WiltonSwitchBox(SwitchBox):
    def __init__(self, x: int, y: int, num_track: int, width: int):
        internal_wires = SwitchBoxHelper.get_wilton_sb_wires(num_track)
        super().__init__(x, y, num_track, width, internal_wires)


class ImranSwitchBox(SwitchBox):
    def __init__(self, x: int, y: int, num_track: int, width: int):
        internal_wires = SwitchBoxHelper.get_imran_sb_wires(num_track)
        super().__init__(x, y, num_track, width, internal_wires)


class Tile:

    def __init__(self, x: int, y: int,
                 track_width: int,
                 switchbox: SwitchBox,
                 height: int = 1):
        self.x = x
        self.y = y
        self.track_width = track_width
        self.height = height

        # create a copy of switch box because the switchbox nodes have to be
        # created
        self.switchbox: SwitchBox = SwitchBox(x, y, switchbox.num_track,
                                              switchbox.width,
                                              switchbox.internal_wires)

        self.ports: Dict[str, PortNode] = {}

        self.inputs = OrderedSet()
        self.outputs = OrderedSet()

        # hold for the core
        self.core: InterconnectCore = None

    def __eq__(self, other):
        if not isinstance(other, Tile):
            return False
        return self.x == other.x and self.y == other.y and \
            self.height == other.height

    def __repr__(self):
        return f"TILE ({self.x}, {self.y}, {self.height}, " +\
               f"{self.switchbox.id})"

    def set_core(self, core: InterconnectCore):
        self.inputs.clear()
        self.outputs.clear()
        self.ports.clear()
        self.core = core

        # this is to clear to core
        if core is None:
            return

        inputs = core.inputs()
        for width, port_name in inputs:
            if width == self.track_width:
                self.inputs.add(port_name)
                # create node
                self.ports[port_name] = PortNode(port_name, self.x,
                                                 self.y, width)
        outputs = core.outputs()
        for width, port_name in outputs:
            if width == self.track_width:
                self.outputs.add(port_name)
                # create node
                self.ports[port_name] = PortNode(port_name, self.x,
                                                 self.y, width)

    def core_has_input(self, port: str):
        return port in self.inputs

    def core_has_output(self, port: str):
        return port in self.outputs

    def name(self):
        return str(self)

    def get_sb(self, side: SwitchBoxSide,
               track: int,
               io: SwitchBoxIO) -> Union[SwitchBoxNode, None]:
        return self.switchbox.get_sb(side, track, io)

    def set_core_connection(self, port_name: str,
                            connection_type: List[SBConnectionType]):
        # make sure that it's an input port
        is_input = self.core_has_input(port_name)
        is_output = self.core_has_output(port_name)

        if not is_input and not is_output:
            # the core doesn't have that port_name
            return
        elif not (is_input ^ is_output):
            raise ValueError("core design error. " + port_name + " cannot be "
                             " both input and output port")

        port_node = self.ports[port_name]
        # add to graph node first, we will handle magma in a different pass
        # based on the graph, since we need to compute the mux height
        for side, track, io in connection_type:
            sb = self.get_sb(side, track, io)
            if is_input:
                sb.add_edge(port_node)
            else:
                port_node.add_edge(sb)

    @staticmethod
    def create_tile(x: int, y: int, bit_width: int, num_tracks: int,
                    internal_wires: List[Tuple[int, SwitchBoxSide,
                                               int, SwitchBoxSide]],
                    height: int = 1) -> "Tile":
        switch = SwitchBox(x, y, num_tracks, bit_width, internal_wires)
        tile = Tile(x, y, bit_width, switch, height)
        return tile


class InterconnectGraph:
    def __init__(self, bit_width: int):
        self.__tiles: Dict[Tuple[int, int], Tile] = {}
        self.__switch_ids: Dict[int, SwitchBox] = {}

        # this is a 2d grid  designed to support fast query with irregular
        # tile height.
        self.__tile_grid: List[List[Union[Tile, None]]] = []

        self.bit_width = bit_width

    def add_tile(self, tile: Tile):
        tile.switchbox.id = self.__assign_id(tile.switchbox)
        x = tile.x
        y = tile.y
        self.__tiles[(x, y)] = tile

        # adjusting __tile_grid
        height = tile.height
        # automatically scale the chip
        while len(self.__tile_grid) < y + height:
            self.__tile_grid.append([])
        for row in range(len(self.__tile_grid)):
            while len(self.__tile_grid[row]) <= x:
                self.__tile_grid[row].append(None)
        # store indices and checking for correctness
        self.__assign_tile_grid(x, y, tile)
        for i in range(y + 1, y + height):
            # adding reference to that tile
            self.__assign_tile_grid(x, i, tile)

    def __assign_tile_grid(self, x: int, y: int, tile: Tile) -> None:
        self.__check_grid(x, y)
        self.__tile_grid[y][x] = tile

    def __check_grid(self, x: int, y: int) -> None:
        if self.__tile_grid[y][x] is not None:
            tile = self.__tile_grid[y][x]
            raise RuntimeError(f"{str(tile)} already exists")

    def __assign_id(self, switch: SwitchBox) -> int:
        for switch_id, s in self.__switch_ids.items():
            if switch == s:
                return switch_id
        switch_id = len(self.__switch_ids)
        self.__switch_ids[switch_id] = switch
        return switch_id

    def get_tile(self, x: int, y: int) -> Union[Tile, None]:
        width, height = self.get_size()
        if x >= width or y >= height:
            return None
        result = self.__tile_grid[y][x]
        return result

    def has_empty_tile(self) -> bool:
        for y in range(len(self.__tile_grid)):
            for x in range(len(self.__tile_grid[y])):
                if self.__tile_grid[y][x] is None:
                    return True
        return False

    def is_original_tile(self, x: int, y: int):
        tile = self.get_tile(x, y)
        return tile is not None and tile.x == x and tile.y == y

    def get_size(self) -> Tuple[int, int]:
        height = len(self.__tile_grid)
        width = len(self.__tile_grid[0])
        return width, height

    def set_core_connection(self, x: int, y: int, port_name: str,
                            connection_type: List[SBConnectionType]):
        tile = self.get_tile(x, y)
        if tile is None:
            # if it's empty, don't do anything
            return
        tile.set_core_connection(port_name, connection_type)

    def set_core_connection_all(self, port_name: str,
                                connection_type: List[Tuple[SwitchBoxSide,
                                                            SwitchBoxIO]]):
        """helper function to set connections for all the tiles with the
        same port_name"""
        for (x, y), tile in self.__tiles.items():
            # construct the connection types
            switch = tile.switchbox
            num_track = switch.num_track
            connections: List[SBConnectionType] = []
            for track in range(num_track):
                for side, io in connection_type:
                    connections.append(SBConnectionType(side, track,
                                                        io))
            self.set_core_connection(x, y, port_name, connections)

    def set_core(self, x: int, y: int, core: InterconnectCore):
        tile = self.get_tile(x, y)
        tile.set_core(core)

    def remove_tile(self, coord: Tuple[int, int]):
        if coord in self.__tiles:
            self.__tiles.pop(coord)

    def get_sb(self, x: int, y: int, side: SwitchBoxSide, track: int,
               io: SwitchBoxIO):
        tile = self.get_tile(x, y)
        if tile is not None:
            return tile.get_sb(side, track, io)
        return None

    def get_port(self, x: int, y: int,
                 port_name: str) -> Union[PortNode, None]:
        tile = self.get_tile(x, y)
        if tile is not None:
            return tile.ports[port_name]
        return None

    def __getitem__(self, item: Tuple[int, int]):
        return self.__tiles[item]

    def __contains__(self, item: Union[Tile, SwitchBox, Node]) -> bool:
        if isinstance(item, Tile):
            x, y = item.x, item.y
            tile = self.get_tile(x, y)
            return tile == item
        x = item.x
        y = item.y
        tile = self.get_tile(x, y)
        if tile is None:
            return False
        if isinstance(item, SwitchBox):
            return tile.switchbox == item
        elif isinstance(item, PortNode):
            return tile.ports[item.name] == item
        elif isinstance(item, RegisterNode):
            return tile.switchbox.registers[item.name] == item
        elif isinstance(item, SwitchBoxNode):
            return tile.get_sb(item.side, item.track, item.io) == item
        return False

    def dump_graph(self, filename: str):
        with open(filename, "w+") as f:
            padding = "  "
            begin = "BEGIN"
            end = "END"

            def write_line(value):
                f.write(value + "\n")

            def write_conn(node_):
                if len(node_) == 0:
                    # don't output if it doesn't have any connections
                    return
                # TODO: need to test if it is deterministic
                write_line(padding + node_.node_str())
                write_line(padding + begin)
                for n in node_:
                    if isinstance(node_, SwitchBoxNode) and \
                            isinstance(n, SwitchBoxNode):
                        if node_.x == n.x and node_.y == n.y:
                            # this is internal connection so we skip
                            continue
                    write_line(padding * 3 + n.node_str())
                write_line(padding + end)

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
            for _, tile in self.__tiles.items():
                write_line(str(tile))
                sbs = tile.switchbox.get_all_sbs()
                for sb in sbs:
                    write_conn(sb)
                for _, node in tile.ports.items():
                    write_conn(node)
                for _, reg in tile.switchbox.registers.items():
                    write_conn(reg)
                for _, reg_mux in tile.switchbox.reg_muxs.items():
                    write_conn(reg_mux)

    def connect_switchbox(self, x0: int, y0: int, x1: int, y1: int,
                          expected_length: int, track: int,
                          policy: InterconnectPolicy):
        """connect switches with expected length in the region
        (x0, y0) <-> (x1, y1), inclusively. it will tries to connect everything
        with expected length. connect in left -> right & top -> bottom fashion.

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

        if (x1 - x0 - 1) % expected_length != 0:
            raise ValueError("the region x has to be divisible by expected_"
                             "length")
        if (y1 - y0 - 1) % expected_length != 0:
            raise ValueError("the region y has to be divisible by expected_"
                             "length")

        # Note (keyi):
        # this code is very complex and hence has many comments. please do not
        # simplify this code unless you fully understand the logic flow.

        # left to right first
        for x in range(x0, x1 - expected_length + 1, expected_length):
            for y in range(y0, y1 + 1, expected_length):
                if not self.is_original_tile(x, y):
                    continue
                tile_from = self.get_tile(x, y)
                tile_to = self.get_tile(x + expected_length, y)
                # several outcomes to consider
                # 1. tile_to is empty -> apply policy
                # 2. tile_to is a reference -> apply policy
                if not self.is_original_tile(x + expected_length, y):
                    if policy == InterconnectPolicy.Ignore:
                        continue
                    # find another tile longer than expected length that's
                    # within the range. because at this point we already know
                    # that the policy is passing through, just search the
                    # nearest tile (not tile reference) to meet the pass
                    # through requirement
                    x_ = x + expected_length
                    while x_ < x1:
                        if self.is_original_tile(x_, y):
                            tile_to = self.__tile_grid[y][x_]
                            break
                        x_ += 1
                    # check again if we have resolved this issue
                    # since it's best effort, we will ignore if no tile left
                    # to connect
                    if not self.is_original_tile(x_, y):
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
        for x in range(x0, x1 + 1):
            for y in range(y0, y1 - expected_length + 1, expected_length):
                if not self.is_original_tile(x, y):
                    continue
                tile_from = self.get_tile(x, y)
                tile_to = self.get_tile(x, y + expected_length)
                # several outcomes to consider
                # 1. tile_to is empty -> apply policy
                # 2. tile_to is a reference -> apply policy
                if not self.is_original_tile(x, y + expected_length):
                    if policy == InterconnectPolicy.Ignore:
                        continue
                    y_ = y + expected_length
                    while y_ < y1:
                        if self.is_original_tile(x, y_):
                            tile_to = self.__tile_grid[y_][x]
                            break
                        y_ += 1
                    # check again if we have resolved this issue
                    # since it's best effort, we will ignore if no tile left
                    # to connect
                    if not self.is_original_tile(x, y_):
                        continue

                assert tile_to.x == tile_from.x
                # add to connection list
                # forward
                self.__add_sb_connection(tile_from, tile_to, track,
                                         SwitchBoxSide.SOUTH)
                # backward
                self.__add_sb_connection(tile_to, tile_from, track,
                                         SwitchBoxSide.NORTH)

    def __add_sb_connection(self, tile_from: Tile,
                            tile_to: Tile, track: int,
                            side: SwitchBoxSide):
        assert tile_from in self
        assert tile_to in self
        # connect the underlying routing graph
        sb_from = tile_from.get_sb(side, track, SwitchBoxIO.SB_OUT)
        sb_to = tile_to.get_sb(SwitchBoxSide.get_opposite_side(side),
                               track, SwitchBoxIO.SB_IN)
        assert sb_from is not None and sb_to is not None
        sb_from.add_edge(sb_to)

    def __iter__(self):
        return iter(self.__tiles)


def mod(a: int, b: int):
    while a < 0:
        a += b
    return a % b


class SwitchBoxHelper:
    """A helper class to create switch box internal connections
    Implementation is copied from Cyclone
    https://github.com/Kuree/cgra_pnr/blob/dev/cyclone/src/util.cc
    """
    @staticmethod
    def get_disjoint_sb_wires(num_tracks: int) -> List[Tuple[int,
                                                             SwitchBoxSide,
                                                             int,
                                                             SwitchBoxSide]]:
        result = []
        for track in range(num_tracks):
            for side_from in SwitchBoxSide:
                for side_to in SwitchBoxSide:
                    if side_from == side_to:
                        continue
                    result.append((track, side_from,
                                   track, side_to))
        return result

    @staticmethod
    def get_wilton_sb_wires(num_tracks: int) -> List[Tuple[int,
                                                           SwitchBoxSide,
                                                           int,
                                                           SwitchBoxSide]]:
        w = num_tracks
        result = []
        # t_i is defined as
        #     3
        #   -----
        # 2 |   | 0
        #   -----
        #     1
        for track in range(num_tracks):
            result.append((track, SwitchBoxSide.WEST,
                           track, SwitchBoxSide.EAST))
            result.append((track, SwitchBoxSide.EAST,
                           track, SwitchBoxSide.WEST))
            # t_1, t_3
            result.append((track, SwitchBoxSide.SOUTH,
                           track, SwitchBoxSide.NORTH))
            result.append((track, SwitchBoxSide.NORTH,
                           track, SwitchBoxSide.SOUTH))
            # t_0, t_1
            result.append((track, SwitchBoxSide.WEST,
                           mod(w - track, w), SwitchBoxSide.SOUTH))
            result.append((mod(w - track, w), SwitchBoxSide.SOUTH,
                           track, SwitchBoxSide.WEST))
            # t_1, t_2
            result.append((track, SwitchBoxSide.SOUTH,
                           mod(track + 1, w), SwitchBoxSide.EAST))
            result.append((mod(track + 1, w), SwitchBoxSide.EAST,
                           track, SwitchBoxSide.SOUTH))
            # t_2, t_3
            result.append((track, SwitchBoxSide.EAST,
                           mod(2 * w - 2 - track, w), SwitchBoxSide.NORTH))
            result.append((mod(2 * w - 2 - track, w), SwitchBoxSide.NORTH,
                           track, SwitchBoxSide.EAST))
            # t3, t_0
            result.append((track, SwitchBoxSide.NORTH,
                          mod(track + 1, w), SwitchBoxSide.WEST))
            result.append((mod(track + 1, w), SwitchBoxSide.WEST,
                           track, SwitchBoxSide.NORTH))
        return result

    @staticmethod
    def get_imran_sb_wires(num_tracks: int) -> List[Tuple[int,
                                                          SwitchBoxSide,
                                                          int,
                                                          SwitchBoxSide]]:
        w = num_tracks
        result = []

        for track in range(num_tracks):
            # f_e1
            result.append((track, SwitchBoxSide.WEST,
                           mod(w - track, w), SwitchBoxSide.NORTH))
            result.append((mod(w - track, w), SwitchBoxSide.NORTH,
                           track, SwitchBoxSide.WEST))
            # f_e2
            result.append((track, SwitchBoxSide.NORTH,
                           mod(track + 1, w), SwitchBoxSide.EAST))
            result.append((mod(track + 1, w), SwitchBoxSide.EAST,
                           track, SwitchBoxSide.NORTH))
            # f_e3
            result.append((track, SwitchBoxSide.SOUTH,
                           mod(w - track - 2, w), SwitchBoxSide.EAST))
            result.append((mod(w - track - 2, w), SwitchBoxSide.EAST,
                           track, SwitchBoxSide.SOUTH))
            # f_e4
            result.append((track, SwitchBoxSide.WEST,
                           mod(track - 1, w), SwitchBoxSide.SOUTH))
            result.append((mod(track - 1, w), SwitchBoxSide.SOUTH,
                           track, SwitchBoxSide.WEST))
            # f_e5
            result.append((track, SwitchBoxSide.WEST,
                           track, SwitchBoxSide.EAST))
            result.append((track, SwitchBoxSide.EAST,
                           track, SwitchBoxSide.WEST))
            # f_e6
            result.append((track, SwitchBoxSide.SOUTH,
                           track, SwitchBoxSide.NORTH))
            result.append((track, SwitchBoxSide.NORTH,
                           track, SwitchBoxSide.SOUTH))
        return result
