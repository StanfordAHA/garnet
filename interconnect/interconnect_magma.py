import magma
import generator.generator as generator
from common.side_type import SideType
from generator.configurable import ConfigurationType


def SideType(num_tracks, layers):
    layers_dict = {f"layer{l}": magma.Array(num_tracks, magma.Bits(l))
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

        for column in self.columns:
            self.wire(self.ports.config, column.ports.config)
        self.wire(self.ports.west, self.columns[0].ports.west)
        self.wire(self.ports.east, self.columns[-1].ports.east)
        for i, column in enumerate(self.columns):
            self.wire(self.ports.north[i], column.ports.north)
            self.wire(self.ports.south[i], column.ports.south)
        for i in range(1, self.width):
            c0 = self.columns[i - 1]
            c1 = self.columns[i]
            for j in range(self.height):
                self.wire(c1.ports.west[j].O, c0.ports.east[j].I)
                self.wire(c0.ports.east[j].O, c1.ports.west[j].I)

    def name(self):
        return "Interconnect_" + "_".join([c.name() for c in self.columns])
