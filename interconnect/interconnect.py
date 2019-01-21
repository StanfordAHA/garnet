from ordered_set import OrderedSet

from .cyclone import InterconnectGraph
from .cyclone import Tile, SwitchBoxNode, SwitchBoxIO
from typing import Dict, Tuple
import generator.generator as generator
from .circuit import TileCircuit, create_name


class Interconnect(generator.Generator):
    def __init__(self, interconnects: Dict[int, InterconnectGraph],
                 addr_width: int, data_width: int):
        super().__init__()

        self.__graphs: Dict[int, InterconnectGraph] = interconnects

        self.__tiles: Dict[Tuple[int, int], Dict[int, Tile]]
        self.tile_circuits: Dict[Tuple[int, int], TileCircuit]

        # loop through the grid and create tile circuits
        # first find all the coordinates
        coordinates = OrderedSet()
        for _, graph in self.__graphs.items():
            for coord in graph:
                coordinates.add(coord)
        # add tiles
        for x, y in coordinates:
            for bit_width, graph in self.__graphs:
                if graph.is_original_tile(x, y):
                    tile = graph[(x, y)]
                    if (x, y) not in self.__tiles:
                        self.__tiles[(x, y)] = {}
                    self.__tiles[(x, y)][bit_width] = tile

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
                        if same_row ^ same_col:
                            raise RuntimeError("Only mesh interconnect is "
                                               "supported")
                        dst_tile = self.tile_circuits[(sb_node.x, sb_node.y)]
                        dst_switch_box = dst_tile.sbs[bit_width]
                        # wire them up
                        idx = sb_node.get_conn_in().index(sb)
                        src_sb_name = create_name(str(sb))
                        dst_sb_name = create_name(str(sb_node))
                        self.wire(switch_box.ports[src_sb_name],
                                  dst_switch_box.ports[dst_sb_name].I[idx])

    def name(self):
        return "Interconnect"
