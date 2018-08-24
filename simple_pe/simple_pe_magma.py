import magma as m
import mantle


def define_pe(ops, T=m.UInt, data_width=16):
    T = T(data_width)
    opcode_width = m.bitutils.clog2(len(ops))

    class PE(m.Circuit):
        name = "PE"
        IO = ["opcode", m.In(m.Bits(opcode_width)), "I0", m.In(T), "I1",
              m.In(T), "O", m.Out(T)]

        @classmethod
        def definition(io):
            # Assumes opcode is equal to index in `ops` list, would be nice to
            # generalize this for different encodings (or opcode orderings)
            O = mantle.mux([op(io.I0, io.I1) for op in ops], io.opcode)
            m.wire(O, io.O)
    return PE
