import magma
import mantle
from gemstone.common.core import ConfigurableCore
from gemstone.common.configurable import ConfigurationType
from gemstone.generator.const import Const
from gemstone.generator.from_magma import FromMagma
from pe_core import pe_core_genesis2
from gemstone.common.coreir_wrap import CoreirWrap


class PECore(ConfigurableCore):
    def __init__(self):
        super().__init__(8, 32)

        # TODO(rsetaluri): Currently we assume the default parameters into the
        # wrapper. Ideally we should take some arguments into this generator
        # and pass them to the genesis wrapper.
        wrapper = pe_core_genesis2.pe_core_wrapper
        generator = wrapper.generator(mode="declare")
        circ = generator()
        self.underlying = FromMagma(circ)

        TData = magma.Bits[16]
        TBit = magma.Bits[1]

        self.add_ports(
            data0=magma.In(TData),
            data1=magma.In(TData),
            bit0=magma.In(TBit),
            bit1=magma.In(TBit),
            bit2=magma.In(TBit),
            res=magma.Out(TData),
            res_p=magma.Out(TBit),
            config=magma.In(ConfigurationType(8, 32)),
            # TODO: Make number of stall domains paramaterizable
            stall=magma.In(magma.Bits[4])
        )

        self.wire(self.ports.data0, self.underlying.ports.data0)
        self.wire(self.ports.data1, self.underlying.ports.data1)
        self.wire(self.ports.bit0[0], self.underlying.ports.bit0)
        self.wire(self.ports.bit1[0], self.underlying.ports.bit1)
        self.wire(self.ports.bit2[0], self.underlying.ports.bit2)
        self.wire(self.ports.res, self.underlying.ports.res)
        self.wire(self.ports.res_p[0], self.underlying.ports.res_p)
        self.wire(self.ports.config.config_addr, self.underlying.ports.cfg_a)
        self.wire(self.ports.config.config_data,
                  self.underlying.ports.cfg_d)
        self.wire(self.ports.config.write[0], self.underlying.ports.cfg_en)
        self.wire(self.underlying.ports.read_data, self.ports.read_config_data)

        self.wire(self.ports.reset, self.underlying.ports.rst)

        # PE core uses clk_en (essentially active low stall)
        self.stallInverter = FromMagma(mantle.DefineInvert(1))
        self.wire(self.stallInverter.ports.I, self.ports.stall[0:1])
        self.wire(self.stallInverter.ports.O[0], self.underlying.ports.clk_en)

    def configure(self, instr):
        raise NotImplementedError()

    def instruction_type(self):
        raise NotImplementedError()

    def inputs(self):
        return [self.ports.data0, self.ports.data1,
                self.ports.bit0, self.ports.bit1, self.ports.bit2]

    def outputs(self):
        return [self.ports.res, self.ports.res_p]

    def name(self):
        return "PECore"
