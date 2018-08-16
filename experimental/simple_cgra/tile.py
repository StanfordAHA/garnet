import generator
import magma
from sb import SB
from side_type import SideType


class Tile(generator.Generator):
    def __init__(self, core):
        super().__init__()

        self.core = core
        self.sb = SB()

        self.add_ports(
            north=SideType(5, (1, 16)),
            west=SideType(5, (1, 16)),
            south=SideType(5, (1, 16)),
            east=SideType(5, (1, 16)),
        )

        self.wire(self.north, self.sb.north)
        self.wire(self.west, self.sb.west)
        self.wire(self.south, self.sb.south)
        self.wire(self.east, self.sb.east)

    def name(self):
        return f"Tile_{self.core.name()}"
