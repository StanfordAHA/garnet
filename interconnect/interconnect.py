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
import magma
import generator.generator as generator
from common.core import Core
from typing import Union, Tuple, NamedTuple, List, Dict, Callable
from generator.configurable import Configurable, ConfigurationType
from common.mux_wrapper import MuxWrapper
from common.zext_wrapper import ZextWrapper
import magma.bitutils

GridCoordinate = Tuple[int, int]


def get_width(t):
    if isinstance(t, magma.BitKind):
        return 1
    if isinstance(t, magma.BitsKind):
        return len(t)
    raise NotImplementedError(t, type(t))


class SwitchBoxSide(enum.Enum):
    """Rename the sides"""
    NORTH = pycyclone.SwitchBoxSide.Top
    SOUTH = pycyclone.SwitchBoxSide.Bottom
    EAST = pycyclone.SwitchBoxSide.Right
    WEST = pycyclone.SwitchBoxSide.Left


def convert_side_to_str(side: Union[SwitchBoxSide,
                                    pycyclone.SwitchBoxSide]) -> str:
    if side == SwitchBoxSide.NORTH or side == pycyclone.SwitchBoxSide.Top:
        return "north"
    elif side == SwitchBoxSide.SOUTH or side == pycyclone.SwitchBoxSide.Bottom:
        return "south"
    elif side == SwitchBoxSide.EAST or side == pycyclone.SwitchBoxSide.Right:
        return "east"
    elif side == SwitchBoxSide.WEST or side == pycyclone.SwitchBoxSide.Left:
        return "west"
    else:
        raise ValueError("unknown value", side)


def get_opposite_side(side: Union[SwitchBoxSide,
                                  pycyclone.SwitchBoxSide]) -> SwitchBoxSide:
    if side == SwitchBoxSide.NORTH:
        return SwitchBoxSide.SOUTH
    elif side == SwitchBoxSide.SOUTH:
        return SwitchBoxSide.NORTH
    elif side == SwitchBoxSide.EAST:
        return SwitchBoxSide.WEST
    elif side == SwitchBoxSide.WEST:
        return SwitchBoxSide.EAST
    elif isinstance(side, pycyclone.SwitchBoxSide):
        return SwitchBoxSide(pycyclone.util.get_opposite_side(side))
    else:
        raise ValueError("unknown value", side)


class SwitchBoxIO(enum.Enum):
    """hides underlying cyclone implementation"""
    IN = pycyclone.SwitchBoxIO.SB_IN
    OUT = pycyclone.SwitchBoxIO.SB_OUT


class Switch:
    def __init__(self, switchbox: pycyclone.Switch):
        super().__init__()
        self.switchbox_ = switchbox
        self.width = switchbox.width
        self.num_track = switchbox.num_track

    def __getitem__(self, value: Tuple[SwitchBoxSide, int,
                                       pycyclone.SwitchBoxIO]):
        side, track, io = value
        side = side.value
        io = io.value
        return self.switchbox_[side, track, io]

    def name(self):
        return self.switchbox_.to_string()


# helper class to create complex switch design
class SwitchManager:
    """A class to manage different types of switch boxes. It is designed to
    handle assigning and recognizing switch IDs. It is because cyclone
    specifies it's the user's responsibility to ensure the uniqueness of
    different switch internal wirings
    """
    def __init__(self):
        self.id_count = 0
        self.sb_wires = {}
        self.default_coord = 0

    def create_disjoint_switch(self, bit_width: int,
                               num_tracks: int) -> Switch:
        internal_connections = pycyclone.util.get_disjoint_sb_wires(num_tracks)
        return self.__create_switch(bit_width, internal_connections, num_tracks)

    def __create_switch(self, bit_width, internal_connections, num_tracks):
        switch_id = self.get_switch_id(internal_connections)
        # x and y will be set when added to a tile, so leave them as 0 here
        return Switch(pycyclone.Switch(self.default_coord, self.default_coord,
                                       num_tracks, bit_width, switch_id,
                                       internal_connections))

    def create_wilton_switch(self, bit_width: int,
                             num_tracks: int) -> Switch:
        internal_connections = pycyclone.util.get_wilton_sb_wires(num_tracks)
        return self.__create_switch(bit_width, internal_connections, num_tracks)

    def create_imran_switch(self, bit_width: int,
                            num_tracks: int) -> Switch:
        internal_connections = pycyclone.util.get_imran_sb_wires(num_tracks)
        return self.__create_switch(bit_width, internal_connections, num_tracks)

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


class Tile:
    """Tile class in a physical layout

    Because a tile can be snapped into different interconnect, i.e. different
    widths, we don't have data width set for the tile. As a result, the inputs
    and outputs set from the core will have mixed-width ports
    """
    def __init__(self, x: int, y: int, height: int):
        self.x = x
        self.y = y
        if height < 1:
            raise RuntimeError(f"height has to be at least 1, got {height}")
        self.height = height
        # we don't set core in the constructor because some tiles may not have
        # core, e.g. IO tiles. Or if we want to create a by-pass tile without
        # core functionality, such as the bottom half of a tall MEM tile
        self.core = None
        self.inputs = {}
        self.outputs = {}

    def set_core(self, core: Core):
        self.core = core
        # automatically creates port names for the core connected
        for input_port in self.core.inputs():
            name = input_port.qualified_name()
            self.inputs[name] = input_port

        for output_port in self.core.outputs():
            name = output_port.qualified_name()
            self.outputs[name] = output_port

    def core_has_input(self, port: str):
        if self.core is None:
            return False
        return port in self.inputs

    def core_has_output(self, port: str):
        if self.core is None:
            return False
        return port in self.outputs

    def name(self):
        return f"Tile ({self.x}, {self.y}, {self.height})"


class SB(Configurable):
    def __init__(self, switchbox: Switch, tile: Tile):
        super().__init__()
        self.switchbox = switchbox
        self.x = switchbox.switchbox_.x
        self.y = switchbox.switchbox_.y

        self.width = switchbox.width
        # Note (keyi):
        # Cyclone supports uneven distribution of switch box connections;
        # that is, one side may have 6 tracks and the other may only have 3.
        # we will restrict this kinds of flexibility here.
        self.num_tracks = switchbox.num_track

        layer_dict = {f"layer{self.width}":
                      magma.Array(self.num_tracks, magma.Bits(self.width))}

        t = magma.Tuple(**layer_dict)

        self.add_ports(
            north=magma.Tuple(**{"I": magma.In(t), "O": magma.Out(t)}),
            west=magma.Tuple(**{"I": magma.In(t), "O": magma.Out(t)}),
            south=magma.Tuple(**{"I": magma.In(t), "O": magma.Out(t)}),
            east=magma.Tuple(**{"I": magma.In(t), "O": magma.Out(t)}),
            clk=magma.In(magma.Clock),
            reset=magma.In(magma.AsyncReset),
            config=magma.In(ConfigurationType(8, 32)),
            read_config_data=magma.Out(magma.Bits(32)),
        )

        self.sides = {SwitchBoxSide.NORTH: self.ports.north,
                      SwitchBoxSide.WEST: self.ports.west,
                      SwitchBoxSide.SOUTH: self.ports.south,
                      SwitchBoxSide.EAST: self.ports.east}

        for port_name, port in tile.outputs.items():
            assert port.type().isoutput()
            self.add_port(port_name, magma.In(port.type()))

        # used for bitstream
        self.reg_config = {}
        # Note:
        # The following logic is different from the previous code, which
        # applies lots of connection logic in the implementation.
        # Here we let the switch box connection to take over
        muxs = self.__create_muxs()
        self.__configure_mux(muxs)
        self.__configure_registers()

    def __create_muxs(self):
        # because in the current design, everything has to go out from an out
        # switch box node, we only enumerate these ones.
        muxs = []
        for side in self.sides:
            for sb in self.switchbox.switchbox_.get_sbs_by_side(side.value):
                if sb.io != pycyclone.SwitchBoxIO.SB_OUT:
                    continue
                conn_ins = sb.get_conn_in()
                height = len(conn_ins)
                muxs.append((MuxWrapper(height, self.width), sb))
        # sort them so that it's consistent with the test model
        # since python sort is stable, we just need to sort by side, this is
        # because in cyclone the sb nodes are arranged in track_num order
        muxs.sort(key=lambda entry: int(entry[1].side))
        return muxs

    def __configure_mux(self,
                        muxs: List[Tuple[MuxWrapper,
                                         pycyclone.SwitchBoxNode]]):
        for mux_idx, (mux, sb) in enumerate(muxs):
            assert sb.width == self.width
            # use the in-coming connections to configure the mux connections
            conn_ins = list(sb.get_conn_in())
            for idx, node in enumerate(conn_ins):
                if node.type == pycyclone.NodeType.SwitchBox:
                    # cast type
                    node = pycyclone.util.convert_to_sb(node)
                    side = SwitchBoxSide(node.side)
                    # the switch box has to be an in direction and cannot be
                    # on the same side
                    assert node.io == SwitchBoxIO.IN.value
                    assert node.side != sb.side
                    mux_in = getattr(self.sides[side].I,
                                     f"layer{self.width}")[node.track]
                    self.wire(mux_in, mux.ports.I[idx])
                elif node.type == pycyclone.NodeType.Port:
                    port_name = node.name
                    self.wire(self.ports[port_name], mux.ports.I[idx])
                else:
                    raise NotImplementedError(str(node.type) + " not "
                                                               "implemented")
            side = SwitchBoxSide(sb.side)
            mux_out = getattr(self.sides[side].O,
                              f"layer{self.width}")[sb.track]
            self.wire(mux.ports.O, mux_out)
            # Add corresponding config register.
            config_name = f"mux_{side.name}_{self.width}_{sb.track}_sel"
            self.add_config(config_name, mux.sel_bits)
            self.wire(self.registers[config_name].ports.O, mux.ports.S)

            # register configuration space
            # we need to keep that since we will need the configuration
            # for bitstream generation
            self.registers[config_name].set_addr(mux_idx)
            self.reg_config[config_name] = mux_idx, str(sb)

    def __configure_registers(self):
        # this is the same as the original implementations
        for idx, reg in enumerate(self.registers.values()):
            reg.set_addr_width(8)
            reg.set_data_width(32)
            self.wire(self.ports.config.config_addr, reg.ports.config_addr)
            self.wire(self.ports.config.config_data, reg.ports.config_data)
            self.wire(self.ports.config.write[0], reg.ports.config_en)
            self.wire(self.ports.reset, reg.ports.reset)

        # read_config_data output
        num_config_reg = len(self.registers)
        if num_config_reg > 1:
            self.read_config_data_mux = MuxWrapper(num_config_reg, 32)
            sel_bits = self.read_config_data_mux.sel_bits
            # Wire up config_addr to select input of read_data MUX
            # TODO(rsetaluri): Make this a mux with default.
            self.wire(self.ports.config.config_addr[:sel_bits],
                      self.read_config_data_mux.ports.S)
            self.wire(self.read_config_data_mux.ports.O,
                      self.ports.read_config_data)
            for idx, reg in enumerate(self.registers.values()):
                zext = ZextWrapper(reg.width, 32)
                self.wire(reg.ports.O, zext.ports.I)
                zext_out = zext.ports.O
                self.wire(zext_out, self.read_config_data_mux.ports.I[idx])
        # If we only have 1 config register, we don't need a mux
        # Wire sole config register directly to read_config_data_output
        else:
            self.wire(self.registers[0].ports.O,
                      self.ports.read_config_data)

    def name(self):
        name = f"SB_{self.x}_{self.y}_{self.width}"
        return name


# TODO (Keyi): the following code looks awfully similar to the one
#              being used in SB. consider refactor!

class CB(Configurable):
    def __init__(self, port: pycyclone.PortNode, sb: SB):
        super().__init__()

        if port.type != pycyclone.NodeType.Port:
            raise ValueError("port has to be a port node")

        # get the incoming connections
        conn_ins = list(port.get_conn_in())
        num_tracks = len(conn_ins)
        if num_tracks <= 1:
            raise ValueError("num_tracks must be > 1")

        # make sure the width is correct
        assert port.width == sb.width

        self.num_tracks = num_tracks
        self.width = port.width
        self.sel_bits = magma.bitutils.clog2(self.num_tracks)

        bits_type = magma.Bits(self.width)

        self.add_ports(
            clk=magma.In(magma.Clock),
            reset=magma.In(magma.AsyncReset),
            config=magma.In(ConfigurationType(8, 32)),
            read_config_data=magma.Out(magma.Bits(32)),
        )

        # PEP8 E741: can't use I or O's for variable names
        self.add_ports(**{
            "I": magma.In(magma.Array(self.num_tracks, bits_type)),
            "O": magma.Out(bits_type)})

        self.mux = self.__create_mux()
        self.__configure_mux(port, sb)
        self.__configure_registers()

    def __create_mux(self):
        mux = MuxWrapper(self.num_tracks, self.width)
        return mux

    def __configure_mux(self, port: pycyclone.PortNode, sb: SB):
        conn_ins = list(port.get_conn_in())
        for idx, node in enumerate(conn_ins):
            if node.type == pycyclone.NodeType.SwitchBox:
                # cast type
                node = pycyclone.util.convert_to_sb(node)
                side = SwitchBoxSide(node.side)
                # Note (keyi):
                # for now we only allow the port to be connected to the switch
                # box node
                assert node.x == port.x
                assert node.y == port.y
                io = "I" if node.io == pycyclone.SwitchBoxIO.SB_IN else "O"

                mux_in = getattr(sb.sides[side][io],
                                 f"layer{self.width}")[node.track]
                self.wire(mux_in, self.mux.ports.I[idx])
            else:
                raise NotImplementedError(str(node.type) + " not "
                                                           "implemented")
        self.add_configs(S=self.sel_bits)

    def __configure_registers(self):
        # read_config_data output
        num_config_reg = len(self.registers)
        if num_config_reg > 1:
            self.read_config_data_mux = MuxWrapper(num_config_reg, 32)
            self.wire(self.ports.config.config_addr,
                      self.read_config_data_mux.ports.S)
            self.wire(self.read_config_data_mux.ports.O,
                      self.ports.read_config_data)
            for idx, reg in enumerate(self.registers.values()):
                self.wire(reg.ports.O, self.read_config_data_mux.ports.I[idx])
                # Wire up config register resets
                self.wire(reg.ports.reset, self.ports.reset)
        # If we only have 1 config register, we don't need a mux
        # Wire sole config register directly to read_config_data_output
        else:
            reg = list(self.registers.values())[0]
            zext = ZextWrapper(reg.width, 32)
            self.wire(reg.ports.O, zext.ports.I)
            zext_out = zext.ports.O
            self.wire(zext_out, self.ports.read_config_data)

        self.wire(self.ports.I, self.mux.ports.I)
        self.wire(self.registers.S.ports.O, self.mux.ports.S)
        self.wire(self.mux.ports.O, self.ports.O)

        for idx, reg in enumerate(self.registers.values()):
            reg.set_addr(idx)
            reg.set_addr_width(8)
            reg.set_data_width(32)
            self.wire(self.ports.config.config_addr, reg.ports.config_addr)
            self.wire(self.ports.config.config_data, reg.ports.config_data)
            # Connect config_en for each config reg
            self.wire(reg.ports.config_en, self.ports.config.write[0])

    def name(self):
        return f"CB_{self.num_tracks}_{self.width}"


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
        self.graph_ = pycyclone.RoutingGraph()

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

        port_node = pycyclone.PortNode(port_name, tile.x, tile.y,
                                       self.track_width)
        # add to graph node first, we will handle magma in a different pass
        # based on the graph, since we need to compute the mux height
        for side, track, io in connection_type:
            sb = pycyclone.SwitchBoxNode(tile.x, tile.y, self.track_width,
                                         track, side.value, io.value)
            if is_input:
                self.graph_.add_edge(sb, port_node)
            else:
                self.graph_.add_edge(port_node, sb)

    def set_core_connection_all(self, port_name: str,
                                connection_type: List[Tuple[SwitchBoxSide,
                                                            SwitchBoxIO]]):
        """helper function to set connections for all the tiles with the
        same port_name"""
        width, height = self.get_size()
        for y in range(height):
            for x in range(width):
                if isinstance(self.grid_[y][x], Tile):
                    # construct the connection types
                    switch = self.get_switch(x, y)
                    num_track = switch.num_track
                    connections: List[SBConnectionType] = []
                    for track in num_track:
                        for side, io in connection_type:
                            connections.append(SBConnectionType(side, track,
                                                                io))
                    self.set_core_connection(x, y, port_name, connections)

    # wrapper function for the underlying cyclone graph
    def get_sb_node(self, x: int, y: int, side: SwitchBoxSide, track: int,
                    io: SwitchBoxIO) -> pycyclone.SwitchBoxNode:
        return self.graph_.get_sb(x, y, side.value, track, io.value)

    def get_port_node(self, x: int, y: int,
                      port_name: str) -> pycyclone.PortNode:
        return self.graph_.get_port(x, y, port_name)

    def get_switch(self, x: int, y: int) -> Switch:
        """return the switch maintained by the underlying routing engine"""
        tile = self.get_cyclone_tile(x, y)
        return Switch(tile.switchbox)

    def realize_sb_cb(self):
        # create sb and cb circuits
        visited = set()
        for y in range(len(self.grid_)):
            for x in range(len(self.grid_[y])):
                tile = self.get_tile(x, y)
                if (tile.x, tile.y) in visited:
                    continue
                switch = self.get_switch(tile.x, tile.y)
                # sb first, then cb
                sb = SB(switch, tile)
                visited.add((tile.x, tile.y))
                self.sbs[(tile.x, tile.y)] = sb
                # cb creation
                for port_node in switch.switchbox_.ports:
                    cb = CB(port_node, sb)
                    self.cbs[(tile.x, tile.y, port_node.name)] = cb
        return self.sbs, self.cbs

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
        sb_from = pycyclone.SwitchBoxNode(tile_from.x, tile_from.y,
                                          self.track_width,
                                          track,
                                          side.value,
                                          SwitchBoxIO.OUT.value)
        sb_to = pycyclone.SwitchBoxNode(tile_to.x, tile_to.y,
                                        self.track_width,
                                        track,
                                        get_opposite_side(side).value,
                                        SwitchBoxIO.IN.value)
        self.graph_.add_edge(sb_from, sb_to)

    def realize_interconnect(self):
        # connect wires based on inter-sb connections
        # we put some restrictions on how switch boxes are connected by
        # checking the connections.
        all_sbs = self.graph_.get_all_sbs()
        for sb_node_from in all_sbs:
            for sb_node_to in sb_node_from:
                # TODO: insert register here?
                if sb_node_to.type != pycyclone.NodeType.SwitchBox:
                    continue
                # it has to be a switch box and we restrict the connection
                # to be sb-out -> sb-in where sb-out and sb-in are in a
                # different tile
                if sb_node_to.x == sb_node_from.x and \
                   sb_node_to.y == sb_node_from.y:
                    raise ValueError("sb connect connect to itself",
                                     sb_node_from, sb_node_to)
                sb_node_to = pycyclone.util.convert_to_sb(sb_node_to)
                track_from = sb_node_from.track
                track_to = sb_node_to.track
                port_from = convert_side_to_str(sb_node_from.side)
                port_to = convert_side_to_str(sb_node_to.side)
                io_from = "I" if sb_node_from.io == SwitchBoxIO.IN.value \
                          else "O"
                io_to = "I" if sb_node_to.io == SwitchBoxIO.IN.value else "O"
                sb_from = self.sbs[(sb_node_from.x, sb_node_from.y)]
                sb_to = self.sbs[(sb_node_to.x, sb_node_to.y)]
                self.wire(sb_from.ports[port_from][io_from][track_from],
                          sb_to.ports[port_to][io_to][track_to])

    def dump_routing_graph(self, filename):
        pycyclone.io.dump_routing_graph(self.graph_, filename)

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


class SwitchBoxType(enum.Enum):
    Disjoint = enum.auto()
    Wilton = enum.auto()
    Imran = enum.auto()


# helper functions to create column-based CGRA interconnect that simplifies
# some of the interface to circuit/cyclone.
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
    sb_manager = SwitchManager()
    # create tiles and set cores
    for x in range(x_offset, width - x_offset):
        for y in range(y_offset, height - y_offset):
            tile = Tile(x, y, tile_height)
            # compute the number of tracks
            num_track = interconnect.compute_num_tracks(x_offset, y_offset,
                                                        x, y, track_info)
            # create switch based on the type passed in
            if sb_type == SwitchBoxType.Disjoint:
                switch = sb_manager.create_disjoint_switch(track_width,
                                                           num_track)
            elif sb_type == SwitchBoxType.Wilton:
                switch = sb_manager.create_wilton_switch(track_width,
                                                         num_track)
            elif sb_type == SwitchBoxType.Imran:
                switch = sb_manager.create_imran_switch(track_width,
                                                        num_track)
            else:
                raise NotImplementedError(sb_type)
            interconnect.add_tile(tile, switch)
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

    # realize the sbs, cbs, and underlying routing graph
    interconnect.realize_sb_cb()
    interconnect.realize_interconnect()

    return interconnect
