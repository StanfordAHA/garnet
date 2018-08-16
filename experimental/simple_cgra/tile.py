import generator
import magma
from sb import SB
from cb import CB
from side_type import SideType


class Tile(generator.Generator):
    def __init__(self, core):
        super().__init__()

        self.core = core
        self.sb = SB()
        self.cbs = [CB(0, 0) for _ in range(len(self.core.inputs()))]

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

        for i, input_ in enumerate(self.core.inputs()):
            self.wire(self.cbs[i].O, input_)

    def name(self):
        return f"Tile_{self.core.name()}"
