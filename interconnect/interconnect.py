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
from typing import Union, Tuple, NamedTuple, List
from generator.configurable import Configurable, ConfigurationType
from common.mux_wrapper import MuxWrapper
from common.zext_wrapper import ZextWrapper

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


class SwitchBoxIO(enum.Enum):
    """hides underlying cyclone implementation"""
    IN = pycyclone.SwitchBoxIO.SB_IN
    OUT = pycyclone.SwitchBoxIO.SB_OUT


class Switch(generator.Generator):
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

    def create_disjoint_switch(self, bit_width: int,
                               num_tracks: int) -> Switch:
        internal_connections = pycyclone.util.get_disjoint_sb_wires(num_tracks)
        switch_id = self.get_switch_id(internal_connections)
        # x and y will be set when added to a tile, so leave them as 0 here
        default_coord = 0
        return Switch(pycyclone.Switch(default_coord, default_coord,
                                       num_tracks, bit_width, switch_id,
                                       internal_connections))

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


# garnet's PEP 8 doesn't like the new way to declare named tuple with type hints
# using the old format
SBConnectionType = NamedTuple("SBConnectionType",
                              [("side", SwitchBoxSide),
                               ("track", int),
                               ("io", SwitchBoxIO)])


class Tile(generator.Generator):
    """Tile class in a physical layout
    Because a tile can be snapped into different interconnect, i.e. different
    widths, we don't have data width set for the tile. As a result, the inputs
    and outputs set from the core will have mixed-width ports
    """
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

        layer_dict = {f"layer{self.width}": magma.Array(self.num_tracks,
                                                        magma.Bits(self.width))}
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
        # The following logic is different from the previous code, which applies
        # lots of connection logic in the implementation.
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
                        muxs: List[Tuple[MuxWrapper, pycyclone.SwitchBoxNode]]):
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

        # placeholders for sb and cb
        self.sbs = []
        self.cbs = []

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
        # make sure that it's an output port
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

    def realize(self):
        # create sb and cb circuits
        visited = set()
        for y in range(len(self.grid_)):
            for x in range(len(self.grid_[y])):
                tile = self.get_tile(x, y)
                if (tile.x, tile.y) in visited:
                    continue
                switch = self.get_switch(tile.x, tile.y)
                sb = SB(switch, tile)
                visited.add((tile.x, tile.y))
                self.sbs.append(sb)
        return self.sbs, self.cbs

    def name(self):
        return f"Interconnect {self.track_width}"
