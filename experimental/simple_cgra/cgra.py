import generator
import magma
from global_controller import GlobalController
from interconnect import Interconnect
from column import Column
from tile import Tile
from pe_core import PECore


Side = magma.Tuple(
    I=magma.In(magma.Array(5, magma.Tuple(layer_1=magma.Bit, layer_16=magma.Bits(16)))),
    O=magma.Out(magma.Array(5, magma.Tuple(layer_1=magma.Bit, layer_16=magma.Bits(16)))))


JTAG = magma.Tuple(
    tdi=magma.Bit,
    tdo=magma.Bit,
    tms=magma.Bit,
    tck=magma.Bit,
    trst_n=magma.Bit)


class CGRA(generator.Generator):
    def __init__(self, width, height):
        super().__init__()

        self.global_controller = GlobalController(32, 32)
        columns = []
        for i in range(width):
            tiles = []
            for j in range(height):
                tiles.append(Tile(PECore()))
            columns.append(Column(tiles))
        self.interconnect = Interconnect(columns)

        self.add_ports(
            north=magma.Array(width, Side),
            south=magma.Array(width, Side),
            west=magma.Array(height, Side),
            east=magma.Array(height, Side),
            jtag_in=magma.In(JTAG),
        )

        self.wire("north", self.interconnect, "north")
        self.wire("south", self.interconnect, "south")
        self.wire("west", self.interconnect, "west")
        self.wire("east", self.interconnect, "east")
        self.wire("jtag_in", self.global_controller, "jtag_in")

    def name(self):
        return "CGRA"


def main():
    cgra = CGRA(4, 4)
    circ = cgra.circuit()
    print (circ)


if __name__ == "__main__":
    main()
