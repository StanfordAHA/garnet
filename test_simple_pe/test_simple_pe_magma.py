from bit_vector import BitVector
from simple_pe.simple_pe_magma import define_pe, define_pe_core
from simple_pe.simple_pe import gen_simple_pe
from common.configurable_circuit import config_ets_template
from common.testers import ResetTester, ConfigurationTester
from fault.test_vector_generator import generate_test_vectors_from_streams
from fault.random import random_bv
import operator
import magma as m
import mantle
import os
import pytest
import fault


simple_ops = [operator.add, operator.sub, operator.and_, operator.or_]
ops = [simple_ops]


@pytest.mark.parametrize("ops", ops)
def test_simple_pe_core(ops):
    pe = define_pe_core(ops, T=m.UInt, data_width=16)

    tester = fault.Tester(pe)

    m.compile("test_simple_pe/build/pe_core", pe, output="coreir",
              passes=["rungenerators", "flatten", "cullgraph"])

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
    opcode_width = m.bitutils.clog2(len(ops))
    op_strs = {
        operator.add: "+",
        operator.sub: "-",
        operator.and_: "&",
        operator.or_: "|"
    }

    problem = """\
[GENERAL]
model_file: pe_core.json
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
    with open("test_simple_pe/build/problem_pe_core.txt", "w") as f:
        f.write(problem)
    assert not os.system(
        "CoSA --problem test_simple_pe/build/problem_pe_core.txt")


@pytest.mark.parametrize("ops", ops)
def test_simple_pe(ops):
    pe = define_pe(ops, T=m.UInt, data_width=16)

    class SimplePETester(ResetTester, ConfigurationTester):
        pass

    pe_functional_model = gen_simple_pe(ops, 16)()

    tester = SimplePETester(pe, pe.clk, pe_functional_model)

    m.compile("test_simple_pe/build/pe", pe, output="coreir",
              passes=["rungenerators", "flatten", "cullgraph"])
    # For some reason cullgraph above doesn't result in a culled output,
    # perhaps coreir running it before rungenerators/flatten?
    os.system("coreir -i test_simple_pe/build/pe.json -o "
              "test_simple_pe/build/pe.json -p cullgraph")

    # For verilator test
    m.compile(f"test_simple_pe/build/{pe.name}", pe, output="coreir-verilog")

    tester.zero_inputs()
    opcode_width = m.bitutils.clog2(len(ops))
    config_addr_width = 1

    for config_data in [BitVector(x, opcode_width) for x in range(0, len(ops))]:
        tester.reset()
        tester.configure(BitVector(0, config_addr_width), config_data)
        tester.test_vectors += \
            generate_test_vectors_from_streams(
                pe, pe_functional_model, {
                    f"I{i}": lambda name, port: random_bv(len(port))
                    for i in range(2)
                })
    tester.compile_and_run(directory="test_simple_pe/build",
                           target="verilator", flags=["-Wno-fatal"])
    opcode_width = m.bitutils.clog2(len(ops))
    op_strs = {
        operator.add: "+",
        operator.sub: "-",
        operator.and_: "&",
        operator.or_: "|"
    }

    for i, op in enumerate(ops):
        with open(f"test_simple_pe/build/conf_{op.__name__}.ets", "w") as ets:
            ets.write(config_ets_template.format(config_addr=0,
                                                 config_addr_width=1,
                                                 config_data=i,
                                                 config_data_width=opcode_width))
        problem = f"""\
[GENERAL]
model_file: pe.json,conf_{op.__name__}.ets

[DEFAULT]
bmc_length: 40
verification: safety

[PE check {op.__name__} configuration]
description: "Check configuring to opcode={i} results in read_data={i}"
formula: (conf_done = 1_1) -> (self.read_data = {i}_{opcode_width})
prove: TRUE
expected: TRUE

[PE check {op.__name__} functionality]
description: "Check configuring to opcode={i} corresponds to {op.__name__}"
formula: (conf_done = 1_1) -> ((self.I0 {op_strs[op]} self.I1) = self.O)
# Assume the previous property
assumptions: (conf_done = 1_1) -> (self.read_data = {i}_{opcode_width})
prove: TRUE
expected: TRUE
"""  # noqa
        problem_file = f"test_simple_pe/build/problem_pe_{op.__name__}.txt"
        with open(problem_file, "w") as f:
            f.write(problem)
        assert not os.system(
            f"CoSA --problem {problem_file}")
