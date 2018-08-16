import generator
import magma
from sb import SB
from cb import CB
from side_type import SideType


def get_width(T):
    if isinstance(T, magma._BitKind):
        return 1
    if isinstance(T, magma.BitsKind):
        return T.N
    raise NotImplementedError(T, type(T))


class Tile(generator.Generator):
    def __init__(self, core):
        super().__init__()

        self.core = core
        self.sb = SB()
        widths = [get_width(i.type()) for i in self.core.inputs()]
        self.cbs = [CB(5, w) for w in widths]

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
            self.wire(self.cbs[i].O[:], input_)

    def features(self):
        return (self.core, self.sb, *(cb for cb in self.cbs))

    def name(self):
        return f"Tile_{self.core.name()}"
