import inspect
import math
import hwtypes
import magma
from gemstone.common.core import ConfigurableCore, PnRTag
from gemstone.common.configurable import ConfigurationType
from gemstone.generator.from_magma import FromMagma
from gemstone.generator.const import Const


class PeakCoreStub(ConfigurableCore):
    def __init__(self):
        super().__init__(8, 32)

        self.add_ports(
            config=magma.In(ConfigurationType(8, 32)),
            data_in=magma.In(magma.Bits[16]),
            data_out=magma.Out(magma.Bits[16]),
        )
        self.wire(self.ports.read_config_data, Const(0))
        self.wire(self.ports.data_out, Const(0))


    
    def configure(self, instr):
        raise NotImplementedError()

    def instruction_type(self):
        raise NotImplementedError()

    def inputs(self):
        return [self.ports.data_in]

    def outputs(self):
        return [self.ports.data_out]

    def pnr_info(self):
        # PE has highest priority
        return PnRTag("p", self.DEFAULT_PRIORITY, self.DEFAULT_PRIORITY)

    def name(self):
        return "PECore"
