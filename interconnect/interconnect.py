import magma
from ordered_set import OrderedSet

from .cyclone import InterconnectGraph, SwitchBoxSide, Node
from .cyclone import Tile, SwitchBoxNode, SwitchBoxIO
from typing import Dict, Tuple
import generator.generator as generator
from .circuit import TileCircuit, create_name
from generator.configurable import ConfigurationType
from generator.const import Const


class Interconnect(generator.Generator):
    def __init__(self, interconnects: Dict[int, InterconnectGraph],
                 addr_width: int, data_width: int, tile_id_width: int,
                 lift_ports=True,
                 fan_out_config=False):
        super().__init__()

        self.data_width = data_width
        self.addr_width = addr_width
        self.tile_id_width = tile_id_width
        self.__graphs: Dict[int, InterconnectGraph] = interconnects

        self.__tiles: Dict[Tuple[int, int], Dict[int, Tile]] = {}
        self.tile_circuits: Dict[Tuple[int, int], TileCircuit] = {}

        # loop through the grid and create tile circuits
        # first find all the coordinates
        coordinates = OrderedSet()
        for _, graph in self.__graphs.items():
            for coord in graph:
                coordinates.add(coord)
        # add tiles
        x_min = 0xFFFF
        x_max = -1
        y_min = 0xFFFF
        y_max = -1

        for x, y in coordinates:
            for bit_width, graph in self.__graphs.items():
                if graph.is_original_tile(x, y):
                    tile = graph[(x, y)]
                    if (x, y) not in self.__tiles:
                        self.__tiles[(x, y)] = {}
                    self.__tiles[(x, y)][bit_width] = tile

            # set the dimensions
            if x > x_max:
                x_max = x
            if x < x_min:
                x_min = x
            if y > y_max:
                y_max = y
            if y < y_min:
                y_min = y
        assert x_max > x_min
        assert y_max > y_min

        self.x_min, self.x_max = x_min, x_max
        self.y_min, self.y_max = y_min, y_max

        # create individual tile circuits
        for coord, tiles in self.__tiles.items():
            self.tile_circuits[coord] = TileCircuit(tiles, addr_width,
                                                    data_width)

        # we need to deal with inter-tile connections now
        # we only limit mesh

        for (x, y), tile in self.tile_circuits.items():
            for bit_width, switch_box in tile.sbs.items():
                all_sbs = switch_box.switchbox.get_all_sbs()
                # TODO: change the search logic once we add pipeline registers
                for sb in all_sbs:
                    if sb.io != SwitchBoxIO.SB_OUT:
                        continue
                    assert x == sb.x and y == sb.y
                    for sb_node in sb:
                        if not isinstance(sb_node, SwitchBoxNode):
                            continue
                        assert sb_node.io == SwitchBoxIO.SB_IN
                        # it has to be a different x or y
                        same_row = sb_node.x == sb.x
                        same_col = sb_node.y == sb.y
                        if not same_row ^ same_col:
                            raise RuntimeError("Only mesh interconnect is "
                                               "supported")
                        dst_tile = self.tile_circuits[(sb_node.x, sb_node.y)]
                        dst_switch_box = dst_tile.sbs[bit_width]
                        # wire them up
                        idx = sb_node.get_conn_in().index(sb)
                        src_sb_name = create_name(str(sb))
                        dst_sb_name = create_name(str(sb_node))
                        #self.wire(switch_box.ports[src_sb_name],
                        #          dst_switch_box.ports[dst_sb_name].I[idx])

        # if we need to lift the ports. this can be used for testing or
        # creating circuit without IO
        # if lift_ports:
        #    self.__lift_ports()

        self.has_fan_out_config = fan_out_config
        if fan_out_config:
            self.__fan_out_config()

        # set tile_id
        self.__set_tile_id()

    @staticmethod
    def __get_tile_id(x: int, y: int):
        return x << 8 | y

    def __set_tile_id(self):
        for (x, y), tile in self.tile_circuits.items():
            tile_id = self.__get_tile_id(x, y)
            self.wire(tile.ports.tile_id,
                      Const(magma.Bits(tile_id, self.tile_id_width)))

    def __lift_ports(self):
        # we assume it's a rectangular grid
        for x in [self.x_min, self.x_max]:
            for y in [self.y_min, self.y_max]:
                if (x, y) in self.tile_circuits:
                    tile = self.tile_circuits[(x, y)]
                    # we only lift sb ports
                    sbs = tile.sbs
                    for bit_width, switchbox in sbs.items():
                        all_sbs = switchbox.switchbox.get_all_sbs()
                        working_set = []
                        if x == self.x_min:
                            # we lift west/left ports
                            for sb_node in all_sbs:
                                if sb_node.side != SwitchBoxSide.WEST:
                                    continue
                                working_set.append(sb_node)
                        elif x == self.x_max:
                            # we lift east/right ports
                            for sb_node in all_sbs:
                                if sb_node.side != SwitchBoxSide.EAST:
                                    continue
                                working_set.append(sb_node)
                        if y == self.y_min:
                            # we lift north/top ports
                            for sb_node in all_sbs:
                                if sb_node.side != SwitchBoxSide.NORTH:
                                    continue
                                working_set.append(sb_node)
                        elif y == self.y_max:
                            # we lift south/bottom ports
                            for sb_node in all_sbs:
                                if sb_node.side != SwitchBoxSide.SOUTH:
                                    continue
                                working_set.append(sb_node)
                        for sb_node in working_set:
                            sb_name = create_name(str(sb_node))
                            sb_port = tile.ports[sb_name]
                            self.add_port(sb_name, sb_port.base_type())
                            self.wire(self.ports[sb_name], sb_port)

    def __fan_out_config(self):
        self.add_ports(
            config=magma.In(ConfigurationType(self.data_width,
                                              self.data_width)),
            clk=magma.In(magma.Clock),
            reset=magma.In(magma.AsyncReset),
            read_config_data=magma.Out(magma.Bits(self.data_width)))

        # fan out wires
        for _, tile_circuit in self.tile_circuits.items():
            self.wire(self.ports.config, tile_circuit.ports.config)
            self.wire(self.ports.reset, tile_circuit.ports.reset)
            self.wire(self.ports.read_config_data,
                      tile_circuit.ports.read_config_data)

    def get_route_bitstream_config(self, src_node: Node, dst_node: Node):
        # this is the complete one which includes the tile_id
        x, y = dst_node.x, dst_node.y
        tile = self.tile_circuits[(x, y)]
        addr, data = tile.get_route_bitstream_config(src_node, dst_node)
        tile_id = self.__get_tile_id(x, y)
        addr = addr | tile_id
        return addr, data

    def name(self):
        return "Interconnect"
