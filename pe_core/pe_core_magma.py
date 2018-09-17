import magma
from common.core import Core
from generator.configurable import ConfigurationType
from generator.const import Const
from generator.from_magma import FromMagma
from pe_core import pe_core_genesis2


class PECore(Core):
    def __init__(self):
        super().__init__()

        # TODO(rsetaluri): Currently we assume the default parameters into the
        # wrapper. Ideally we should take some arguments into this generator and
        # pass them to the genesis wrapper.
        wrapper = pe_core_genesis2.pe_core_wrapper
        type_map = {
            "clk": magma.In(magma.Clock),
        }
        generator = wrapper.generator(mode="declare", type_map=type_map)
        circ = generator()
        self.underlying = FromMagma(circ)

        TData = magma.Bits(16)
        TBit = magma.Bits(1)

        self.add_ports(
            data0=magma.In(TData),
            data1=magma.In(TData),
            data2=magma.In(TData),
            bit0=magma.In(TBit),
            bit1=magma.In(TBit),
            bit2=magma.In(TBit),
            res=magma.Out(TData),
            res_p=magma.Out(TBit),
            clk=magma.In(magma.Clock),
            config=magma.In(ConfigurationType(8, 32)),
            read_config_data=magma.Out(magma.Bits(32)),
        )

        self.wire(self.ports.data0, self.underlying.ports.data0)
        self.wire(self.ports.data1, self.underlying.ports.data1)
        self.wire(self.ports.data2, self.underlying.ports.data2)
        self.wire(self.ports.bit0[0], self.underlying.ports.bit0)
        self.wire(self.ports.bit1[0], self.underlying.ports.bit1)
        self.wire(self.ports.bit2[0], self.underlying.ports.bit2)
        self.wire(self.ports.res, self.underlying.ports.res)
        self.wire(self.ports.res_p[0], self.underlying.ports.res_p)
        self.wire(self.ports.config.config_addr, self.underlying.ports.cfg_a)
        self.wire(self.ports.config.config_data,
                  self.underlying.ports.cfg_d)
        self.wire(self.underlying.ports.read_data, self.ports.read_config_data)

        # TODO(rsetaluri): Actually wire these inputs.
        signals = (
            ("rst_n", 1),
            ("clk_en", 1),
            ("cfg_en", 1),
        )
        for name, width in signals:
            val = magma.bits(0, width) if width > 1 else magma.bit(0)
            self.wire(Const(val), self.underlying.ports[name])

    def inputs(self):
        return [self.ports.data0, self.ports.data1, self.ports.data2,
                self.ports.bit0, self.ports.bit1, self.ports.bit2]

    def outputs(self):
        return [self.ports.res, self.ports.res_p]

    def name(self):
        return "PECore"
