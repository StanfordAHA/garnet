import generator
import magma
from global_controller import GlobalController
from interconnect import Interconnect
from column import Column
from tile import Tile
from pe_core import PECore
from mem_core import MemCore
from side_type import SideType
from jtag_type import JTAGType


class CGRA(generator.Generator):
    def __init__(self, width, height):
        super().__init__()

        self.global_controller = GlobalController(32, 32)
        columns = []
        for i in range(width):
            tiles = []
            for j in range(height):
                core = PECore() if (i + j) % 2 else MemCore()
                tiles.append(Tile(core))
            columns.append(Column(tiles))
        self.interconnect = Interconnect(columns)

        side_type = self.interconnect.side_type
        self.add_ports(
            north=magma.Array(width, side_type),
            south=magma.Array(width, side_type),
            west=magma.Array(height, side_type),
            east=magma.Array(height, side_type),
            jtag_in=magma.In(JTAGType),
            clk=magma.In(magma.Clock),
        )

        self.wire(self.north, self.interconnect.north)
        self.wire(self.south, self.interconnect.south)
        self.wire(self.west, self.interconnect.west)
        self.wire(self.east, self.interconnect.east)
        self.wire(self.jtag_in, self.global_controller.jtag_in)

        # Global wires.
        self.fanout(self.clk, (self.interconnect, self.global_controller))
        self.interconnect.add_ports(config=self.global_controller.config_type)
        self.wire(self.global_controller.config, self.interconnect.config)
        self.interconnect.fanout(self.interconnect.clk, self.interconnect.columns)
        self.interconnect.fanout(self.interconnect.config,
                                 self.interconnect.columns)
        for column in self.interconnect.columns:
            column.fanout(column.clk, column.tiles)
            column.fanout(column.config, column.tiles)
            for tile in column.tiles:
                tile.fanout(tile.clk, tile.features())
                tile.fanout(tile.config, tile.features())
                for feature in tile.features():
                    registers = feature.registers.values()
                    feature.fanout(feature.clk, registers)
                    feature.fanout(feature.config.config_addr, registers)
                    feature.fanout(feature.config.config_data, registers)
                    for register in feature.registers.values():
                        register.addr = 0

    def name(self):
        return "CGRA"


def main():
    cgra = CGRA(4, 4)
    circ = cgra.circuit()
    print (circ)


if __name__ == "__main__":
    main()
