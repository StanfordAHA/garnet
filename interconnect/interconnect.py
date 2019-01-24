import magma
from ordered_set import OrderedSet
import os
from .cyclone import InterconnectGraph, SwitchBoxSide, Node
from .cyclone import Tile, SwitchBoxNode, SwitchBoxIO, RegisterMuxNode
from typing import Dict, Tuple, List
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
                    # we need to be carefully about looping through the
                    # connections
                    # if the switch box has pipeline registers, we need to
                    # do a "jump" over the connected switch
                    # format: dst_node, src_port_name, src_node
                    neighbors: List[Tuple[Node, str, Node]] = []
                    for node in sb:
                        if isinstance(node, SwitchBoxNode):
                            neighbors.append((node, create_name(str(sb)), sb))
                        elif isinstance(node, RegisterMuxNode):
                            # making sure the register is inserted properly
                            assert len(sb) == 2
                            # we need to make a jump here
                            for n in node:
                                neighbors.clear()
                                if isinstance(n, SwitchBoxNode):
                                    neighbors.append((n, create_name(str(sb)),
                                                      node))
                            break
                    for sb_node, src_sb_name, src_node in neighbors:
                        assert isinstance(sb_node, SwitchBoxNode)
                        assert sb_node.io == SwitchBoxIO.SB_IN
                        # it has to be a different x or y
                        same_row = sb_node.x == sb.x
                        same_col = sb_node.y == sb.y
                        if not same_row ^ same_col:
                            raise RuntimeError("Only mesh interconnect is "
                                               "supported")
                        # notice that we already lift the ports up
                        # since we are not dealing with internal connections
                        # using the tile-level port is fine
                        dst_tile = self.tile_circuits[(sb_node.x, sb_node.y)]
                        # wire them up
                        idx = sb_node.get_conn_in().index(src_node)
                        dst_sb_name = create_name(str(sb_node))
                        self.wire(tile.ports[src_sb_name],
                                  dst_tile.ports[dst_sb_name][idx])

        # if we need to lift the ports. this can be used for testing or
        # creating circuit without IO
        if lift_ports:
            self.__lift_ports()

        self.has_fan_out_config = fan_out_config
        if fan_out_config:
            self.__fan_out_config()

        # set tile_id
        self.__set_tile_id()

    def __get_tile_id(self, x: int, y: int):
        return x << (self.tile_id_width // 2) | y

    def __set_tile_id(self):
        for (x, y), tile in self.tile_circuits.items():
            tile_id = self.__get_tile_id(x, y)
            self.wire(tile.ports.tile_id,
                      Const(magma.bits(tile_id, self.tile_id_width)))

    def find_exterior_sb_nodes(self):
        # this is useful for lifting ports and testing
        # we assume it's a rectangular grid
        # we only care about the perimeter
        x_range = {self.x_min, self.x_max}
        y_range = {self.y_min, self.y_max}
        coordinates = OrderedSet()
        for (x, y) in self.tile_circuits:
            if x in x_range or y in y_range:
                coordinates.append((x, y))
        working_set = []

        for x, y in coordinates:
            tile = self.tile_circuits[(x, y)]
            # we only lift sb ports
            sbs = tile.sbs
            for bit_width, switchbox in sbs.items():
                all_sbs = switchbox.switchbox.get_all_sbs()
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
        return working_set

    def __lift_ports(self):
        working_set = self.find_exterior_sb_nodes()
        for sb_node in working_set:
            x, y = sb_node.x, sb_node.y
            tile = self.tile_circuits[(x, y)]
            sb_name = create_name(str(sb_node))
            sb_port = tile.ports[sb_name]
            self.add_port(sb_name, sb_port.base_type())
            self.wire(self.ports[sb_name], sb_port)

    def __fan_out_config(self):
        self.add_ports(
            config=magma.In(ConfigurationType(self.data_width,
                                              self.data_width)),
            clk=magma.In(magma.Clock),
            reset=magma.In(magma.AsyncReset))

        # fan out wires
        for _, tile_circuit in self.tile_circuits.items():
            self.wire(self.ports.config, tile_circuit.ports.config)
            self.wire(self.ports.reset, tile_circuit.ports.reset)

    def get_route_bitstream_config(self, src_node: Node, dst_node: Node):
        # this is the complete one which includes the tile_id
        x, y = dst_node.x, dst_node.y
        tile = self.tile_circuits[(x, y)]
        entry = tile.get_route_bitstream_config(src_node, dst_node)
        if entry is None:
            return None
        addr, data = entry
        tile_id = self.__get_tile_id(x, y)
        addr = addr | tile_id
        return addr, data

    def dump_pnr(self, dir_name, design_name):
        # TODO: add layout dump as well
        if not os.path.isdir(dir_name):
            os.mkdir(dir_name)
        graph_path_dict = {}
        for bit_width, graph in self.__graphs.items():
            graph_path = os.path.join(dir_name, f"{bit_width}.graph")
            graph_path_dict[bit_width] = graph_path
            graph.dump_graph(graph_path)

        pnr_file = os.path.join(dir_name, f"{design_name}.info")
        with open(pnr_file, "w+") as f:
            graph_configs = [f"{bit_width} {graph_path_dict[bit_width]}" for
                             bit_width in self.__graphs]
            graph_config_str = " ".join(graph_configs)
            f.write(f"graph={graph_config_str}\n")

    def name(self):
        return "Interconnect"
