import magma
import mantle
from common.mux_wrapper import MuxWrapper
import generator.generator as generator
from generator.const import Const
from generator.from_magma import FromMagma


class MuxWithDefaultWrapper(generator.Generator):
    """
    This generator returns a circuit with the following semantics"

      if(S < height & EN):
          O = I[S]
      else:
          O = default

    There is a constraint on the parameters such that we require that

      2 ^ `sel_bits` > `num_inputs`

    This ensures that there are enough incoming select bits to choose between
    the inputs *and* the default value.
    """
    def __init__(self, num_inputs, width, sel_bits, default):
        super().__init__()

        self.num_inputs = num_inputs
        self.width = width
        self.sel_bits = sel_bits
        self.default = default

        if 2 ** self.sel_bits <= self.num_inputs:
            raise ValueError(f"(2 ^ sel_bits) must be > num_inputs "
                             f"(sel_bits={self.sel_bits}, "
                             f"num_inputs={self.num_inputs})")

        self.data_mux = MuxWrapper(self.num_inputs, self.width)
        self.default_mux = MuxWrapper(2, self.width)
        lt = mantle.DefineULT(self.sel_bits)
        and_gate = mantle.DefineAnd(2)
        self.lt = FromMagma(lt)
        self.and_gate = FromMagma(and_gate)

        T = magma.Bits(self.width)
        self.add_ports(
            I=magma.In(magma.Array(self.num_inputs, T)),
            S=magma.In(magma.Bits(self.sel_bits)),
            EN=magma.In(magma.Bits(1)),
            O=magma.Out(T),
        )

        # Wire data inputs to data mux.
        for i in range(self.num_inputs):
            self.wire(self.ports.I[i], self.data_mux.ports.I[i])

        # Wire select input to select input of data_mux. Note that we only wire
        # the first clog2(num_inputs) bits of the select input.
        self.wire(self.ports.S[:self.data_mux.sel_bits], self.data_mux.ports.S)

        # Wire default value to first input of default mux, and output of
        # data_mux to second input of default mux.
        default_mux_inputs = [
            Const(magma.bits(self.default, self.width)),
            self.data_mux.ports.O,
        ]
        for i, mux_in in enumerate(default_mux_inputs):
            self.wire(mux_in, self.default_mux.ports.I[i])

        # Generate select logic for default mux:
        #   sel = (S < num_inputs) & EN
        self.wire(self.ports.S, self.lt.ports.I0)
        self.wire(Const(magma.bits(self.num_inputs, self.sel_bits)),
                  self.lt.ports.I1)
        self.wire(self.lt.ports.O, self.and_gate.ports.I0)
        self.wire(self.ports.EN[0], self.and_gate.ports.I1)
        self.wire(self.and_gate.ports.O, self.default_mux.ports.S[0])
        self.wire(self.default_mux.ports.O, self.ports.O)

    def name(self):
        return f"MuxWithDefaultWrapper"\
            f"_{self.num_inputs}"\
            f"_{self.width}"\
            f"_{self.sel_bits}"\
            f"_{self.default}"
