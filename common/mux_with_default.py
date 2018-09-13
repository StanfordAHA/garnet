import magma
import mantle
from common.mux_wrapper import MuxWrapper
import generator.generator as generator
from generator.const import Const
from generator.from_magma import FromMagma


class mux_with_default_wrapper(generator.Generator):
    def __init__(self, height, width, default=0):
        super().__init__()

        self.data_mux = MuxWrapper(height, width)
        self.default_mux = MuxWrapper(2, width)
        self.sel_bits = self.data_mux.sel_bits
        lt = mantle.ULT(self.sel_bits+1)
        and_gate = mantle.And(2)
        self.lt = FromMagma(lt)
        self.and_gate = FromMagma(and_gate)

        T = magma.Bits(width)
        self.add_ports(
            I=magma.In(magma.Array(height, T)),
            S=magma.In(magma.Bits(self.sel_bits)),
            EN=magma.In(1),
            O=magma.Out(T)
        )
        # Wire data inputs to data mux
        for i in range(self.height):
            self.wire(self.ports.I[i], self.data_mux.ports[f"I{i}"])
        # wire select input to select input of data_mux
        self.wire(self.ports.S, self.data_mux.ports.S)
        # wire default value of first input of default mux
        self.wire(Const(magma.bits(default, 32)),
                  self.read_config_data_mux.ports.I[0])
        # wire output of data_mux to second input of default mux
        self.wire(self.data_mux.ports.O, self.default_mux.ports.I[1])
        # if(S < height & EN):
        #     O = I[S]
        # else:
        #     O = default
        self.wire(self.ports.S, self.lt.ports.I0)
        self.wire(Const(magma.bits(height, self.sel_bits+1)),
                  self.lt.ports.I1)
        self.wire(self.lt.ports.O, self.and_gate.ports.I0)
        self.wire(self.ports.EN, self.and_gate.ports.I1)
        self.wire(self.and_gate.ports.O, self.default_mux.ports.S)
