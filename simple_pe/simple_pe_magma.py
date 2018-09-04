import magma as m
import mantle
from common.configurable_circuit import ConfigInterface


def make_name(base_name, ops, T, data_width):
    return f"{base_name}__ops_{'_'.join(op.__name__ for op in ops)}__" \
           f"{type(T).__name__}_{data_width}"


def define_pe_core(ops, T=m.UInt, data_width=16):
    T = T(data_width)
    opcode_width = m.bitutils.clog2(len(ops))

    class PECore(m.Circuit):
        name = make_name("PECore", ops, T, data_width)
        IO = ["opcode", m.In(m.Bits(opcode_width)), "I0", m.In(T), "I1",
              m.In(T), "O", m.Out(T)]

        @classmethod
        def definition(io):
            # Assumes opcode is equal to index in `ops` list, would be nice to
            # generalize this for different encodings (or opcode orderings)
            O = mantle.mux([op(io.I0, io.I1) for op in ops], io.opcode)
            m.wire(O, io.O)
    return PECore


def define_pe(ops, T=m.UInt, data_width=16):
    PECore = define_pe_core(ops, T, data_width)
    T = T(data_width)
    opcode_width = m.bitutils.clog2(len(ops))
    config_addr_width = 1

    class PE(m.Circuit):
        name = make_name("PE", ops, T, data_width)
        IO = ["I0", m.In(T), "I1", m.In(T), "O", m.Out(T),
              # We use explicit names here instead of m.ClockInterface so it
              # matches the interfaces of the genesis circuits
              # TODO: We could define a custom ClockInterface for garnet, so at
              # least everything is in sync and can be changed in one place
              "clk", m.In(m.Clock), "reset", m.In(m.AsyncReset)]
        IO += ConfigInterface(config_addr_width, opcode_width)

        @classmethod
        def definition(io):
            config = mantle.Register(opcode_width,
                                     has_ce=True,
                                     has_async_reset=True)

            config_addr_zero = m.bits(0, config_addr_width) == io.config_addr
            opcode = config(io.config_data,
                            CE=(m.bit(io.config_en) & config_addr_zero))
            # TODO: Automatically create instances and wires for configuration
            # logic. E.g. it could automatically create the register and wire
            # it up to read_data
            m.wire(opcode, io.read_data)
            m.wire(PECore()(opcode, io.I0, io.I1), io.O)
    return PE
