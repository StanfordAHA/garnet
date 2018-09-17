import magma
import mantle
import generator.generator as generator
from common.side_type import SideType
from generator.configurable import ConfigurationType
from generator.from_magma import FromMagma
from generator.const import Const


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
            rst=magma.In(magma.Reset),
            read_config_data=magma.Out(magma.Bits(32)),
            column_num=magma.In(magma.Bits(8)),
        )

        self.read_data_OR = FromMagma(mantle.DefineOr(self.height, 32))
        self.wire(self.read_data_OR.ports.O, self.ports.read_config_data)
        for tile in self.tiles:
            self.wire(self.ports.config, tile.ports.config)
        self.wire(self.ports.north, self.tiles[0].ports.north)
        self.wire(self.ports.south, self.tiles[-1].ports.south)
        for i, tile in enumerate(self.tiles):
            self.wire(self.ports.west[i], tile.ports.west)
            self.wire(self.ports.east[i], tile.ports.east)
            self.wire(tile.ports.read_config_data,
                      self.read_data_OR.ports[f"I{i}"])
            # Wire upper 8 bits of tile ID to row number
            self.wire(tile.ports.tile_id[8:16], Const(magma.bits(i, 8)))
            # Wire lower 8 bits of tile ID to col number
            self.wire(tile.ports.tile_id[0:8], self.ports.column_num)
        for i in range(1, self.height):
            t0 = self.tiles[i - 1]
            t1 = self.tiles[i]
            self.wire(t1.ports.north.O, t0.ports.south.I)
            self.wire(t0.ports.south.O, t1.ports.north.I)

    def name(self):
        return "Column_" + "_".join([t.name() for t in self.tiles])
