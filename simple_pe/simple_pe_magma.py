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
            O = m.bits(0, data_width)  # default
            for i, op in enumerate(ops):
                O = mantle.mux([O, op(io.I0, io.I1)],
                               io.opcode == m.bits(i, opcode_width))
            m.wire(O, io.O)
    return PE
