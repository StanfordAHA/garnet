import magma as m
from generator import Generator


class GlobalController(Generator):
    def __init__(self, addr_width=32, data_width=32):
        super().__init__()
        self.__addr_width = 32
        self.__data_width = 32
        self.__jtag_inputs = {
            "tdi": m.In(m.Bit),
            "tdo": m.In(m.Bit),
            "tms": m.In(m.Bit),
            "tck": m.In(m.Bit),
            "trst_n": m.In(m.Bit)
        }

    @property
    def addr_width(self):
        return self.__addr_width

    @property
    def data_width(self):
        return self.__data_width

    @property
    def jtag_inputs(self):
        return self.__jtag_inputs.copy()

    def _generate_impl(self):
        TAddr = m.Bits(self.__addr_width)
        TData = m.Bits(self.__data_width)

        class _GlobalController(m.Circuit):
            name = "GlobalController"
            IO = []

            # Inputs coming from JTAG.
            for name_, type_ in self.jtag_inputs.items():
                IO += [name_, type_]

            # Debug config data input (comes from tiles).
            IO += ["config_data_in", m.In(TData)]

            # Config related outputs.
            IO += ["read", m.Out(m.Bit),
                   "write", m.Out(m.Bit),
                   "cgra_stalled", m.Out(m.Bits(4)),
                   "config_addr_out", m.Out(TAddr),
                   "config_data_out", m.Out(TData)]

            @classmethod
            def definition(io):
                # TODO(rsetaluri): Implement GC logic.
                m.wire(0, io.read)
                m.wire(0, io.write)
                m.wire(m.bits(0, 4), io.cgra_stalled)
                m.wire(m.bits(0, TAddr.N), io.config_addr_out)
                m.wire(m.bits(0, TData.N), io.config_data_out)

        return _GlobalController
