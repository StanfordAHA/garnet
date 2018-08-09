import generator
import magma
from side_type import SideType


class Interconnect(generator.Generator):
    def __init__(self, columns):
        super().__init__()

        assert all([c.height == columns[0].height for c in columns])
        self.width = len(columns)
        self.height = columns[0].height
        self.columns = columns

        self.add_ports(
            north=magma.Array(self.width, SideType(5, (1, 16))),
            south=magma.Array(self.width, SideType(5, (1, 16))),
            west=magma.Array(self.height, SideType(5, (1, 16))),
            east=magma.Array(self.height, SideType(5, (1, 16))),
        )

        self.wire(self.west, self.columns[0].west)
        self.wire(self.east, self.columns[-1].east)
        for i, column in enumerate(self.columns):
            self.wire(self.north[i], column.north)
            self.wire(self.south[i], column.south)
        for i in range(1, self.width):
            c0 = self.columns[i - 1]
            c1 = self.columns[i]
            self.wire(c0.east, c1.west)

    def name(self):
        return "Interconnect"
