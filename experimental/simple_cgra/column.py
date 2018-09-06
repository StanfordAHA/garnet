import generator
import magma
from side_type import SideType
from configurable import ConfigurationType


class Column(generator.Generator):
    def __init__(self, tiles):
        super().__init__()

        self.tiles = tiles
        self.height = len(tiles)

        self.add_ports(
            north=SideType(5, (1, 16)),
            south=SideType(5, (1, 16)),
            west=magma.Array(self.height, SideType(5, (1, 16))),
            east=magma.Array(self.height, SideType(5, (1, 16))),
            config=magma.In(ConfigurationType(32, 32)),
            clk=magma.In(magma.Clock),
        )

        self.fanout(self.config, self.tiles)
        self.wire(self.north, self.tiles[0].north)
        self.wire(self.south, self.tiles[-1].south)
        for i, tile in enumerate(self.tiles):
            self.wire(self.west[i], tile.west)
            self.wire(self.east[i], tile.east)
        for i in range(1, self.height):
            t0 = self.tiles[i - 1]
            t1 = self.tiles[i]
            self.wire(t1.north.O, t0.south.I)
            self.wire(t0.south.O, t1.north.I)

    def name(self):
        return "Column_" + "_".join([t.name() for t in self.tiles])
