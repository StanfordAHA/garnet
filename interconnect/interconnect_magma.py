import magma
import mantle
import generator.generator as generator
from common.side_type import SideType
from generator.configurable import ConfigurationType
from generator.const import Const
from generator.from_magma import FromMagma


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
            reset=magma.In(magma.AsyncReset),
            read_config_data=magma.Out(magma.Bits(32)),
            # TODO: make number of stall domains a param
            stall=magma.In(magma.Bits(4))
        )

        for column in self.columns:
            self.wire(self.ports.config, column.ports.config)
            self.wire(self.ports.reset, column.ports.reset)
            self.wire(self.ports.stall, column.ports.stall)
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

        # OR together read_data outputs from each column
        # number of inputs = number of columns
        self.read_data_OR = FromMagma(mantle.DefineOr(len(self.columns), 32))
        for i, col in enumerate(columns):
            self.wire(self.read_data_OR.ports[f"I{i}"],
                      col.ports.read_config_data)
            # wire up column number input
            self.wire(col.ports.column_num, Const(magma.bits(i, 8)))
        self.wire(self.read_data_OR.ports.O, self.ports.read_config_data)

    def name(self):
        return "Interconnect_" + "_".join([c.name() for c in self.columns])
