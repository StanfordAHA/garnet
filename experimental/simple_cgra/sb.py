import generator
import magma
from side_type import SideType


class SB(generator.Generator):
    def __init__(self):
        super().__init__()

        self.add_ports(
            north=SideType(5, (1, 16)),
            west=SideType(5, (1, 16)),
            south=SideType(5, (1, 16)),
            east=SideType(5, (1, 16)),
        )

        self.wire(self.north.I, self.south.O)
        self.wire(self.west.I, self.east.O)
        self.wire(self.south.I, self.north.O)
        self.wire(self.east.I, self.west.O)

    def name(self):
        return f"SB"
