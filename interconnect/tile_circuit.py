from common.core import Core
from typing import List, Dict, NamedTuple, Union, Tuple
from common.mux_wrapper import MuxWrapper
from common.zext_wrapper import ZextWrapper
from .cyclone import PortNode, Switch as GSwitch
from .circuit import CB, Circuit, EmptyCircuit, Connectable, SwitchBoxMux
from .circuit import RegisterCircuit, MuxBlock
from .sb import SB
from .cyclone import SwitchBoxSide, SwitchBoxIO, Tile as GTile
from generator.configurable import Configurable, ConfigurationType
import magma


class SBConnectionType(NamedTuple):
    side: SwitchBoxSide
    track: int
    io: SwitchBoxIO


class TileCircuit(Configurable):
    def __init__(self, tile: GTile):
        super().__init__()
        self.g_tile = tile
        self.x = tile.x
        self.y = tile.y
        self.track_width = tile.track_width
        self.height = tile.height

        # because at this point the switchbox have already been created
        # we will go ahead and create switch box mux for them
        self.switchbox = SB(tile.switchbox)

        self.port_circuits: Dict[str, Connectable] = {}
        self.reg_circuits: Dict[str, Connectable] = {}

        # if there is any
        for _, port_node in self.g_tile.ports.items():
            self.__create_circuit_from_port(port_node)

        # holds the core
        self.core: Core = None

        # holds the realized circuits
        self.sb_muxs: List[MuxBlock] = []
        self.cb_muxs: List[MuxBlock] = []

        self.read_config_data_mux: MuxWrapper = None
        # ports for reconfiguration
        self.add_ports(
            clk=magma.In(magma.Clock),
            reset=magma.In(magma.AsyncReset),
        )

    def get_sb_circuit(self, side: SwitchBoxSide, track: int, io: SwitchBoxIO):
        return self.switchbox[side.value][io.value][track]

    def get_all_sb_circuits(self) -> List[SwitchBoxMux]:
        result = []
        for track in range(self.switchbox.g_switch.num_track):
            for side in range(GSwitch.NUM_SIDES):
                for io in range(GSwitch.NUM_IOS):
                    result.append(self.switchbox[side][io][track])
        return result

    def get_port_circuit(self, port_name) -> Connectable:
        return self.port_circuits[port_name]

    def __create_circuit_from_port(self, port_node: PortNode):
        # if it's an output port, we use empty circuit instead
        is_input = self.g_tile.core_has_input(port_node.name)
        is_output = self.g_tile.core_has_output(port_node.name)
        assert is_input ^ is_output
        port_ref = self.g_tile.port_references[port_node.name]
        if is_input:
            self.port_circuits[port_node.name] = CB(port_node, port_ref)
        else:
            self.port_circuits[port_node.name] = EmptyCircuit(port_node,
                                                              port_ref)

    def set_core(self, core: Core):
        # reset the ports, if not empty
        self.port_circuits.clear()
        # store the core
        self.core = core
        # create graph nodes based on the core inputs/outputs
        self.g_tile.set_core(core)
        for _, port_node in self.g_tile.ports.items():
            self.__create_circuit_from_port(port_node)

    def set_core_connection(self, port_name: str,
                            connection_type: List[SBConnectionType]):
        # make sure that it's an input port
        is_input = self.g_tile.core_has_input(port_name)
        is_output = self.g_tile.core_has_output(port_name)

        if not is_input and not is_output:
            # the core doesn't have that port_name
            return
        elif not (is_input ^ is_output):
            raise ValueError("core design error. " + port_name + " cannot be "
                             " both input and output port")

        port_node = self.get_port_circuit(port_name)
        # add to graph node first, we will handle magma in a different pass
        # based on the graph, since we need to compute the mux height
        for side, track, io in connection_type:
            sb = self.get_sb_circuit(side, track, io)
            if is_input:
                sb.connect(port_node)
            else:
                port_node.connect(sb)

    @staticmethod
    def create(sb: SB, height: int = 1) -> "TileCircuit":
        """helper class to create tile circuit without touch cyclone graph"""
        if not isinstance(sb, SB):
            raise TypeError(sb, SB)
        tile = GTile(sb.x, sb.y, sb.track_width, sb.g_switch, height)
        return TileCircuit(tile)

    def realize(self):
        self.sb_muxs = self.switchbox.realize()
        # sort it so that it will always be in order
        port_names = sorted(self.port_circuits.keys())
        for port_name in port_names:
            port = self.port_circuits[port_name]
            mux = port.realize()
            if isinstance(mux, MuxBlock):
                self.cb_muxs.append(mux)
        # TODO: add register circuit here
        # copy the wires over so that the generator works properly
        for sb_mux in self.sb_muxs:
            self.wires += sb_mux.wires
        for _, circuit in self.port_circuits.items():
            if isinstance(circuit, CB):
                if circuit.mux.height == 0:
                    # it nothing comes to that cb, don't create that circuit
                    continue
            self.wires += circuit.wires

        return self.sb_muxs, self.cb_muxs

    def __contains__(self, item: Union[Circuit, Core]):
        if isinstance(item, (CB, EmptyCircuit)):
            port_name = item.node.name
            return self.port_circuits[port_name] == item
        elif isinstance(item, RegisterCircuit):
            reg_name = item.node.name
            return self.reg_circuits[reg_name] == item
        elif isinstance(item, SwitchBoxMux):
            return item in self.switchbox
        elif isinstance(item, Core) and self.core is not None:
            return self.core == Core
        else:
            return False

    def add_config_reg(self, addr_width, data_width):
        """called after the circuit is realized"""
        self.add_ports(
            config=magma.In(ConfigurationType(addr_width, data_width)),
            read_config_data=magma.Out(magma.Bits(data_width)),
        )
        # sb_muxs and cb_muxs are created in order,
        # so it is deterministic
        for circuit in self.sb_muxs:
            config_name = self.get_mux_sel_name(circuit)
            if circuit.mux.sel_bits > 0:
                self.add_config(config_name, circuit.mux.sel_bits)
                self.wire(self.registers[config_name].ports.O,
                          circuit.mux.ports.S)
            else:
                # we don't care about pass-through wires
                assert circuit.mux.height <= 1

        for circuit in self.cb_muxs:
            config_name = self.get_mux_sel_name(circuit)
            if circuit.mux.sel_bits > 0:
                self.add_config(config_name, circuit.mux.sel_bits)
                self.wire(self.registers[config_name].ports.O,
                          circuit.mux.ports.S)
            else:
                # we don't care about pass-through wires
                assert circuit.mux.height <= 1

        # sort the registers by it's name. this will be the order of config
        # addr index
        config_names = list(self.registers.keys())
        config_names.sort()
        for idx, config_name in enumerate(config_names):
            reg = self.registers[config_name]
            # set the configuration registers
            reg.set_addr(idx)
            reg.set_addr_width(addr_width)
            reg.set_data_width(data_width)

            self.wire(self.ports.config.config_addr, reg.ports.config_addr)
            self.wire(self.ports.config.config_data, reg.ports.config_data)
            self.wire(self.ports.config.write[0], reg.ports.config_en)
            self.wire(self.ports.reset, reg.ports.reset)

        # read_config_data output
        num_config_reg = len(self.registers)
        if num_config_reg > 1:
            self.read_config_data_mux = MuxWrapper(num_config_reg, data_width)
            sel_bits = self.read_config_data_mux.sel_bits
            # Wire up config_addr to select input of read_data MUX
            self.wire(self.ports.config.config_addr[:sel_bits],
                      self.read_config_data_mux.ports.S)
            self.wire(self.read_config_data_mux.ports.O,
                      self.ports.read_config_data)

            for idx, config_name in enumerate(config_names):
                reg = self.registers[config_name]
                zext = ZextWrapper(reg.width, data_width)
                self.wire(reg.ports.O, zext.ports.I)
                zext_out = zext.ports.O
                self.wire(zext_out, self.read_config_data_mux.ports.I[idx])
        else:
            self.wire(self.registers[config_names[0]].ports.O,
                      self.ports.read_config_data)

    def get_conn_config(self,
                        circuit_from: Connectable,
                        circuit_to: Connectable) -> Tuple[int, int, str]:
        """returns bitstream values and annotation"""
        if circuit_to not in self:
            raise ValueError(str(circuit_to) + " doesn't exist in " + str(self))
        if isinstance(circuit_to, EmptyCircuit):
            # src will never be connected to
            raise ValueError(str(circuit_to) + " cannot be the src")
        else:
            assert isinstance(circuit_to, MuxBlock)
            if not circuit_from.is_connected(circuit_to):
                msg = str(circuit_from) + " is not connected to "\
                    + str(circuit_to)
                raise ValueError(msg)
            node_from = circuit_from.node
            node_to = circuit_to.node
            conn_ins = node_to.get_conn_in()
            mux_idx = conn_ins.index(node_from)
            mux_sel_name = self.get_mux_sel_name(circuit_to)
            reg = self.registers[mux_sel_name]
            reg_addr = reg.addr
            # annotation string
            annotation = f"connect {str(circuit_to)} to {str(circuit_from)}"
            return reg_addr, mux_idx, annotation

    @staticmethod
    def get_mux_sel_name(circuit: Circuit):
        return f"{circuit.name()}_sel"

    def name(self):
        return f"Tile_{self.x}_{self.y}"
