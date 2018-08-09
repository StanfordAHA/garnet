import generator
import magma


Side = magma.Tuple(
    I=magma.In(magma.Array(5, magma.Tuple(layer_1=magma.Bit, layer_16=magma.Bits(16)))),
    O=magma.Out(magma.Array(5, magma.Tuple(layer_1=magma.Bit, layer_16=magma.Bits(16)))))


class Column(generator.Generator):
    def __init__(self, tiles):
        super().__init__()

        self.tiles = tiles
        self.height = len(tiles)

        self.add_ports(
            north=Side,
            south=Side,
            west=magma.Array(self.height, Side),
            east=magma.Array(self.height, Side),
        )

        self.wire(self.north, self.tiles[0].north)
        self.wire(self.south, self.tiles[-1].south)
        for i, tile in enumerate(self.tiles):
            self.wire(self.west[i], tile.west)
            self.wire(self.east[i], tile.east)
        for i in range(1, self.height):
            t0 = self.tiles[i - 1]
            t1 = self.tiles[i]
            self.wire(t0.south, t1.north)

    def name(self):
        return "Column"
