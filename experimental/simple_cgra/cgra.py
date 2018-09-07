import generator
import magma
from my_global_controller import MyGlobalController
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

        self.global_controller = MyGlobalController(32, 32)
        columns = []
        for i in range(width):
            tiles = []
            for j in range(height):
                core = MemCore() if (i % 2) else PECore()
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
        self.wire(self.global_controller.config, self.interconnect.config)

    def name(self):
        return "CGRA"


def main():
    cgra = CGRA(4, 4)
    cgra_circ = cgra.circuit()
    magma.compile("cgra", cgra_circ, output="coreir-verilog", split="build/")


if __name__ == "__main__":
    main()
