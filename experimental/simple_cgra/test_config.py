import generator
import magma
import mantle
from from_magma import FromMagma
from configurable import Configurable


class TileGenerator(Configurable):
    def __init__(self, width):
        super().__init__()

        self.width = width
        T = magma.Bits(width)

        self.add_ports(
            I=magma.In(T),
            O=magma.Out(T),
        )

        self.add_configs(
            operand0=self.width,
            operand1=self.width,
        )
        self.registers["operand0"].addr = 0
        self.registers["operand1"].addr = 0

        self.and_ = FromMagma(mantle.DefineAnd(3, width))

        self.wire(self.I, self.and_.I0)
        self.wire(self.operand0, self.and_.I1)
        self.wire(self.operand1, self.and_.I2)
        self.wire(self.and_.O, self.O)

    def name(self):
        return f"Tile_{self.width}"


class TopGenerator(Configurable):
    def __init__(self):
        super().__init__()

        width = 16
        T = magma.Bits(width)

        self.tiles = [TileGenerator(width) for _ in range(10)]

        self.add_ports(
            I0=magma.In(T),
            I1=magma.In(T),
            I2=magma.In(T),
            I3=magma.In(T),
            O=magma.Out(T),
        )

        self.add_configs(
            sel=2,
        )
        self.registers["sel"].addr = 0

        self.mux = FromMagma(mantle.DefineMux(4, width))

        for tile in self.tiles:
            self.wire(self.config_addr, tile.config_addr)
            self.wire(self.config_data, tile.config_data)
        for tile in self.tiles:
           self.wire(self.config_addr, tile.config_addr)
           self.wire(self.config_data, tile.config_data)
        self.wire(self.I0, self.mux.I0)
        self.wire(self.I1, self.mux.I1)
        self.wire(self.I2, self.mux.I2)
        self.wire(self.I3, self.mux.I3)
        self.wire(self.sel, self.mux.S)
        self.wire(self.mux.O, self.tiles[0].I)
        self.wire(self.tiles[-1].O, self.O)
        for i in range(1, len(self.tiles)):
           m0 = self.tiles[i - 1]
           m1 = self.tiles[i]
           self.wire(m0.O, m1.I)

    def name(self):
        return "Top"


if __name__ == "__main__":
    top_gen = TopGenerator()
    top_circ = top_gen.circuit()
    magma.compile("top", top_circ, output="coreir")
    print(open("top.json").read())
