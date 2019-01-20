"""
This is a layer build on top of Cyclone
"""
from common.zext_wrapper import ZextWrapper
from generator.configurable import Configurable, ConfigurationType
from .cyclone import Node, PortNode, Tile, SwitchBoxNode, SwitchBoxIO
from .cyclone import SwitchBox
from generator.port_reference import PortReferenceBase
from common.mux_wrapper import MuxWrapper
import magma
from typing import Dict, Tuple, Union
from abc import abstractmethod
import generator.generator as generator


def create_name(name: str):
    tokens = " (),"
    for t in tokens:
        name = name.replace(t, "_")
    return name


def get_mux_sel_name(node: Node):
    return f"{create_name(str(node))}_sel"


def create_mux(node: Node):
    conn_in = node.get_conn_in()
    height = len(conn_in)
    mux = MuxWrapper(height, node.width)
    return mux


class InterconnectConfigurable(Configurable):
    def __init__(self, addr_width: int, data_width: int):
        super().__init__()
        self.addr_width = addr_width
        self.data_width = data_width

        self.read_config_data_mux: MuxWrapper = None

        # ports for reconfiguration
        self.add_ports(
            clk=magma.In(magma.Clock),
            reset=magma.In(magma.AsyncReset),
        )

    def _setup_config(self):
        # sort the registers by it's name. this will be the order of config
        # addr index
        config_names = list(self.registers.keys())
        config_names.sort()
        for idx, config_name in enumerate(config_names):
            reg = self.registers[config_name]
            # set the configuration registers
            reg.set_addr(idx)
            reg.set_addr_width(self.addr_width)
            reg.set_data_width(self.data_width)

            self.wire(self.ports.config.config_addr, reg.ports.config_addr)
            self.wire(self.ports.config.config_data, reg.ports.config_data)
            self.wire(self.ports.config.write[0], reg.ports.config_en)
            self.wire(self.ports.reset, reg.ports.reset)

        # read_config_data output
        num_config_reg = len(config_names)
        if num_config_reg > 1:
            self.read_config_data_mux = MuxWrapper(num_config_reg,
                                                   self.data_width)
            sel_bits = self.read_config_data_mux.sel_bits
            # Wire up config_addr to select input of read_data MUX
            self.wire(self.ports.config.config_addr[:sel_bits],
                      self.read_config_data_mux.ports.S)
            self.wire(self.read_config_data_mux.ports.O,
                      self.ports.read_config_data)

            for idx, config_name in enumerate(config_names):
                reg = self.registers[config_name]
                zext = ZextWrapper(reg.width, self.data_width)
                self.wire(reg.ports.O, zext.ports.I)
                zext_out = zext.ports.O
                self.wire(zext_out, self.read_config_data_mux.ports.I[idx])
        else:
            config_name = config_names[0]
            reg = self.registers[config_name]
            zext = ZextWrapper(reg.width, self.data_width)
            self.wire(reg.ports.O, zext.ports.I)
            zext_out = zext.ports.O
            self.wire(zext_out, self.ports.read_config_data)

    @abstractmethod
    def name(self):
        pass


class CB(InterconnectConfigurable):
    def __init__(self, node: PortNode,
                 addr_width: int, data_width: int):
        if not isinstance(node, PortNode):
            raise ValueError(node, PortNode.__name__)
        super().__init__(addr_width, data_width)

        self.node = node
        self.mux = create_mux(self.node)

        # lift the port to the top level
        self.add_ports(
            I=self.mux.ports.I.base_type(),
            O=self.mux.ports.O.base_type())

        self.wire(self.ports.I, self.mux.ports.I)
        self.wire(self.ports.O, self.mux.ports.O)

        if self.mux.height > 1:
            self.add_ports(
                config=magma.In(ConfigurationType(addr_width, data_width)),
                read_config_data=magma.Out(magma.Bits(data_width)),
            )
            config_name = get_mux_sel_name(self.node)
            self.add_config(config_name, self.mux.sel_bits)
            self.wire(self.registers[config_name].ports.O,
                      self.mux.ports.S)

        self._setup_config()

    def name(self):
        return create_name(self.node.name)


class SB(InterconnectConfigurable):
    def __init__(self, switchbox: SwitchBox, addr_width: int, data_width: int):
        super().__init__(addr_width, data_width)
        self.switchbox = switchbox

        # lift the ports up
        sbs = self.switchbox.get_all_sbs()
        self.sb_muxs: Dict[str, Tuple[SwitchBoxNode, MuxWrapper]] = {}
        # first pass to create the mux circuit
        for sb in sbs:
            sb_name = str(sb)
            self.sb_muxs[sb_name] = (sb, create_mux(sb))
        # second pass to lift the ports and wire them
        self.sb_names = []
        for sb_name, (sb, mux) in self.sb_muxs.items():
            # only lift them if the ports are connect to the outside world
            if sb.io == SwitchBoxIO.SB_IN:
                self.add_port(sb_name, mux.ports.I.base_type())
                self.wire(self.ports[sb_name], mux.ports.I)

                self.sb_names.append((sb_name, SwitchBoxIO.SB_IN))
            else:
                self.add_port(sb_name, mux.ports.O.base_type())
                self.wire(self.ports[sb_name], mux.ports.O)

                self.sb_names.append((sb_name, SwitchBoxIO.SB_OUT))

        # connect internal sbs
        self.__connect_sbs()

        # set up the configuration registers
        self.add_ports(
            config=magma.In(ConfigurationType(addr_width, data_width)),
            read_config_data=magma.Out(magma.Bits(data_width)),
        )
        for _, (sb, mux) in self.sb_muxs.items():
            config_name = get_mux_sel_name(sb)
            if mux.height > 1:
                assert mux.sel_bits > 0
                self.add_config(config_name, mux.sel_bits)
                self.wire(self.registers[config_name].ports.O,
                          mux.ports.S)

        self._setup_config()

    def name(self):
        return str(self.switchbox)

    def __connect_sbs(self):
        # the principle is that it only connects to the nodes within
        # its range. for instance, in SB we only connect to sb nodes
        for _, (sb, mux) in self.sb_muxs.items():
            if sb.io == SwitchBoxIO.SB_IN:
                for node in sb:
                    if not isinstance(node, SwitchBoxNode):
                        continue
                    assert node.io == SwitchBoxIO.SB_OUT
                    assert node.x == sb.x and node.y == sb.y
                    input_port = mux.ports.O
                    idx = node.get_conn_in().index(sb)
                    node_, mux = self.sb_muxs[str(node)]
                    assert node_ == node
                    output_port = mux.ports.I[idx]
                    self.wire(input_port, output_port)


class TileCircuit(generator.Generator):
    """We merge tiles at the same coordinates with different bit widths
    The only requirements is that the tiles have to be on the same
    coordinates. Their heights do not have to match.
    """
    def __init__(self, tiles: Dict[int, Tile],
                 addr_width: int, data_width: int):
        super().__init__()

        self.tiles = tiles
        self.addr_width = addr_width
        self.data_width = data_width

        # sanity check
        x = -1
        y = -1
        for bit_width, tile in self.tiles.items():
            assert bit_width == tile.track_width
            if x == -1:
                x = tile.x
                y = tile.y
            else:
                assert x == tile.x
                assert y == tile.y

        assert x != -1 and y != -1
        self.x = x
        self.y = y

        # create cb and switchbox
        self.cbs: Dict[str, CB] = {}
        self.sbs: Dict[str, SB] = {}
        # we only create cb if it's an input port, which doesn't have
        # graph neighbors
        for bit_width, tile in self.tiles.items():
            core = tile.core
            # connection box time
            for port_name, port_node in tile.ports.items():
                # input ports
                if len(port_node) == 0:
                    # make sure that it has at least one connection
                    assert len(port_node.get_conn_in()) > 0
                    assert bit_width == port_node.width

                    # create a CB
                    port_ref = core.get_port_ref(port_node.name)
                    cb = CB(port_node, addr_width, data_width)
                    self.wire(cb.ports.O, port_ref)
                    self.cbs[cb.name()] = cb
                else:
                    # output ports
                    assert len(port_node.get_conn_in()) == 0
                    assert bit_width == port_node.width

                    # no nothing as we will handle the connections later
            # switch box time
            sb = SB(tile.switchbox, addr_width, data_width)
            self.sbs[sb.name()] = sb

        # lift all the ports up
        # connection box time
        for cb_name, cb in self.cbs.items():
            self.add_port(cb_name, cb.ports.I.base_type())
            self.wire(self.ports[cb_name], cb.ports.I)

        # switch box time
        for _, sb in self.sbs.items():
            for sb_name, io in sb.sb_names:
                if io == SwitchBoxIO.SB_IN:
                    self.add_port(sb_name, sb.ports.I.base_type())
                    self.wire(self.ports[sb_name], sb.ports.I)
                else:
                    self.add_port(sb_name, sb.ports.O.base_type())
                    self.wire(self.ports[sb_name], sb.ports.O)

        # connect ports (either from core or cb) to switch box
        for cb_name, cb in self.cbs.items():
            for node in cb.node:
                assert node.x == self.x and node.y == self.y
                assert isinstance(node, SwitchBoxNode)
                # locate the switch box
                found = False
                for _, sb in self.sbs.items():
                    if sb.switchbox.width == node.width:
                        found = True
                        # connect them
                        sb_name = str(node)
                        self.wire(self.ports[cb_name], sb.ports[sb_name])

                assert found

    def name(self):
        return f"TILE {self.x} {self.y}"
