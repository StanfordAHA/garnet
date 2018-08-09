import generator
import magma
from side_type import SideType


class Tile(generator.Generator):
    def __init__(self, core):
        super().__init__()
        self.core = core

        self.add_ports(
            north=SideType(5, (1, 16)),
            west=SideType(5, (1, 16)),
            south=SideType(5, (1, 16)),
            east=SideType(5, (1, 16)),
        )

        self.wire(self.north, self.south)
        self.wire(self.west, self.east)

    def name(self):
        return f"Tile_{self.core.name()}"
