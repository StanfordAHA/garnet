import generator
import magma
from tile import Tile


Side = magma.Tuple(
    I=magma.In(magma.Array(5, magma.Tuple(layer_1=magma.Bit, layer_16=magma.Bits(16)))),
    O=magma.Out(magma.Array(5, magma.Tuple(layer_1=magma.Bit, layer_16=magma.Bits(16)))))


class Interconnect(generator.Generator):
    def __init__(self, columns):
        super().__init__()

        assert all([c.height == columns[0].height for c in columns])
        self.width = len(columns)
        self.height = columns[0].height
        self.columns = columns

        self.add_ports(
            north=magma.Array(self.width, Side),
            south=magma.Array(self.width, Side),
            west=magma.Array(self.height, Side),
            east=magma.Array(self.height, Side),
        )

        self.wire("west", self.columns[0], "west")
        self.wire("east", self.columns[-1], "east")
        for i, column in enumerate(self.columns):
            self.wire(f"north[{i}]", column, "north")
            self.wire(f"south[{i}]", column, "south")
        for i in range(1, self.width):
            c0 = self.columns[i - 1]
            c1 = self.columns[i]
            generator.wire(c0, "east", c1, "west")

    def name(self):
        return "Interconnect"
