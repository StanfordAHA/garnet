import magma
import generator.generator as generator
from common.side_type import SideType
from generator.configurable import ConfigurationType


def SideType(num_tracks, layers):
    layers_dict = {f"layer{l}" : magma.Array(num_tracks, magma.Bits(l)) \
                   for l in layers}
    T = magma.Tuple(**layers_dict)
    return magma.Tuple(I=magma.In(T), O=magma.Out(T))


class Interconnect(generator.Generator):
    def __init__(self, columns):
        super().__init__()

        assert all([c.height == columns[0].height for c in columns])
        self.width = len(columns)
        self.height = columns[0].height
        self.columns = columns
        self.side_type = SideType(5, (1, 16))

        self.add_ports(
            north=magma.Array(self.width, self.side_type),
            south=magma.Array(self.width, self.side_type),
            west=magma.Array(self.height, self.side_type),
            east=magma.Array(self.height, self.side_type),
            config=magma.In(ConfigurationType(32, 32)),
            clk=magma.In(magma.Clock),
            rst=magma.In(magma.Reset),
        )

        self.fanout(self.config, self.columns)
        self.wire(self.west, self.columns[0].west)
        self.wire(self.east, self.columns[-1].east)
        for i, column in enumerate(self.columns):
            self.wire(self.north[i], column.north)
            self.wire(self.south[i], column.south)
        for i in range(1, self.width):
            c0 = self.columns[i - 1]
            c1 = self.columns[i]
            for j in range(self.height):
                self.wire(c1.west[j].O, c0.east[j].I)
                self.wire(c0.east[j].O, c1.west[j].I)

    def name(self):
        return "Interconnect_" + "_".join([c.name() for c in self.columns])
