import magma
import generator.generator as generator
from simple_sb.simple_sb_magma import SB
from simple_cb.simple_cb_magma import CB
from common.side_type import SideType
from generator.configurable import ConfigurationType


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
        self.sb = SB(self.core.outputs())
        widths = [get_width(i.type()) for i in self.core.inputs()]
        self.cbs = [CB(10, w) for w in widths]

        self.add_ports(
            north=SideType(5, (1, 16)),
            west=SideType(5, (1, 16)),
            south=SideType(5, (1, 16)),
            east=SideType(5, (1, 16)),
            config=magma.In(ConfigurationType(32, 32)),
            clk=magma.In(magma.Clock),
            rst=magma.In(magma.Reset),
            read_config_data=magma.Out(32)
        )

        self.wire(self.ports.north, self.sb.ports.north)
        self.wire(self.ports.west, self.sb.ports.west)
        self.wire(self.ports.south, self.sb.ports.south)
        self.wire(self.ports.east, self.sb.ports.east)

        sides = (self.ports.north, self.ports.west)
        for i, cb in enumerate(self.cbs):
            side = sides[i % len(sides)]
            self.__wire_cb(side, cb)

        for i, input_ in enumerate(self.core.inputs()):
            self.wire(self.cbs[i].ports.O, input_)

        for i, out in enumerate(self.core.outputs()):
            self.wire(out, self.sb.ports[out._name])

        for feature in self.features():
            self.wire(self.ports.config.config_addr[24:32],
                      feature.ports.config.config_addr)
            self.wire(self.ports.config.config_data,
                      feature.ports.config.config_data)

    def __wire_cb(self, side, cb):
        if cb.width == 1:
            self.wire(side.I.layer1, cb.ports.I[:5])
            # TODO(rsetaluri): Use anonymous ports instead.
            self.wire(self.sb.ports[side._name].O.layer1, cb.ports.I[5:])
        elif cb.width == 16:
            self.wire(side.I.layer16, cb.ports.I[:5])
            # TODO(rsetaluri): Use anonymous ports instead.
            self.wire(self.sb.ports[side._name].O.layer16, cb.ports.I[5:])
        else:
            raise NotImplementedError(cb, cb.width)

    def features(self):
        return (self.core, self.sb, *(cb for cb in self.cbs))

    def name(self):
        return f"Tile_{self.core.name()}"
