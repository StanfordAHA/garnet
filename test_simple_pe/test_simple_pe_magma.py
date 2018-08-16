from simple_pe.simple_pe_magma import define_pe
import fault.random
import operator
import magma as m
import mantle
import os


def test_simple_pe():
    ops = [operator.add, operator.sub, operator.and_, operator.or_]
    pe = define_pe(ops, T=m.UInt, data_width=16)

    tester = fault.Tester(pe)

    # Sanity check each op with random value
    for i, op in enumerate(ops):
        tester.poke(pe.opcode, i)
        I0 = fault.random.random_bv(16)
        I1 = fault.random.random_bv(16)
        tester.poke(pe.I0, I0)
        tester.poke(pe.I1, I1)
        tester.eval()
        tester.expect(pe.O, op(I0, I1))
    tester.compile_and_run(target="coreir")

    m.compile("test_simple_pe/build/pe", pe, output="coreir")
    assert not os.system("coreir -i test_simple_pe/build/pe.json "
                         "-o test_simple_pe/build/pe_flat.json "
                         "-p rungenerators,flatten,cullgraph -l commonlib")
    opcode_width = m.bitutils.clog2(len(ops))
    op_strs = {
        operator.add: "+",
        operator.sub: "-",
        operator.and_: "&",
        operator.or_: "|"
    }

    problem = """\
[GENERAL]
model_file: pe_flat.json

[DEFAULT]
bmc_length: 30
verification: safety

"""
    for i, op in enumerate(ops):
        problem += f"""\
[PE check {op.__name__}]
description: "Check opcode={i} corresponds to {op.__name__}"
formula: (self.opcode = {i}_{opcode_width}) -> ((self.I0 {op_strs[op]} self.I1) = self.O)
prove: TRUE
expected: TRUE

[PE check {op.__name__} is possible]
description: "Avoid vacuosly true version of above property"
formula: (self.opcode != {i}_{opcode_width})
prove: TRUE
expected: FALSE


"""  # noqa
    with open("test_simple_pe/build/problem.txt", "w") as f:
        f.write(problem)
    assert not os.system(
        "python CoSA/CoSA.py --problem test_simple_pe/build/problem.txt")
