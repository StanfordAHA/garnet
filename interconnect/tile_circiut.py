from common.core import Core
from typing import List, Dict
from .cyclone import PortNode, Switch as GSwitch
from .circuit import CB, Circuit, EmptyCircuit, Connectable, SwitchBoxMux
from .sb import SB
from .cyclone import SwitchBoxSide, SwitchBoxIO, Tile as GTile
import generator.generator as generator


class TileCircuit(Circuit):
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

        self.ports: Dict[str, Connectable] = {}
        self.registers: Dict[str, Connectable] = {}

        # if there is any
        for _, port_node in self.g_tile.ports.items():
            self.__create_circuit_from_port(port_node)

        # holds the core
        self.core: Core = None

        # holds the realized circuits
        self.sb_muxs: List[generator.Generator] = []
        self.cb_muxs: List[generator.Generator] = []

    def get_sb_circuit(self, side: SwitchBoxSide, track: int, io: SwitchBoxIO):
        return self.switchbox[side.value][io.value][track]

    def get_all_sb_circuits(self) -> List[SwitchBoxMux]:
        result = []
        for track in range(self.switchbox.g_switch.num_track):
            for side in range(GSwitch.NUM_SIDES):
                for io in range(GSwitch.NUM_IOS):
                    result.append(self.switchbox[side][io][track])
        return result

    def get_port_circuit(self, port_name):
        return self.ports[port_name]

    def __create_circuit_from_port(self, port_node: PortNode):
        # if it's an output port, we use empty circuit instead
        is_input = self.g_tile.core_has_input(port_node.name)
        is_output = self.g_tile.core_has_output(port_node.name)
        assert is_input ^ is_output
        if is_input:
            self.ports[port_node.name] = CB(port_node)
        else:
            self.ports[port_node.name] = EmptyCircuit(port_node)

    def set_core(self, core: Core):
        # reset the ports, if not empty
        self.ports.clear()
        # store the core
        self.core = core
        # create graph nodes based on the core inputs/outputs
        self.g_tile.set_core(core)
        for _, port_node in self.g_tile.ports.items():
            self.__create_circuit_from_port(port_node)

    @staticmethod
    def create(sb: SB, height: int = 1) -> "TileCircuit":
        """helper class to create tile circuit without touch cyclone graph"""
        if not isinstance(sb, SB):
            raise TypeError(sb, SB)
        tile = GTile(sb.x, sb.y, sb.track_width, sb.g_switch, height)
        return TileCircuit(tile)

    def realize(self):
        sbs = self.get_all_sb_circuits()
        for sb in sbs:
            mux = sb.realize()
            self.sb_muxs.append(mux)
        for _, port in self.ports.items():
            mux = port.realize()
            if mux is not None:
                self.cb_muxs.append(mux)
        # TODO: add register circuit here
        return self.sb_muxs + self.cb_muxs

    def name(self):
        return self.create_name(str(self.g_tile))
