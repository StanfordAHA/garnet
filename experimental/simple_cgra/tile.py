import generator
import magma


Side = magma.Tuple(
    I=magma.In(magma.Array(5, magma.Tuple(layer_1=magma.Bit, layer_16=magma.Bits(16)))),
    O=magma.Out(magma.Array(5, magma.Tuple(layer_1=magma.Bit, layer_16=magma.Bits(16)))))


class Tile(generator.Generator):
    def __init__(self, core):
        super().__init__()
        self.core = core

        self.add_ports(
            north=Side,
            west=Side,
            south=Side,
            east=Side,
        )

        self.wire(self.north, self.south)
        self.wire(self.west, self.east)

    def name(self):
        return f"Tile_{self.core.name()}"
