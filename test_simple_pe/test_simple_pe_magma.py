from bit_vector import BitVector
from simple_pe.simple_pe_magma import define_pe, define_pe_core
from simple_pe.simple_pe import gen_simple_pe
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
              coreir_args={"passes": ["rungenerators", "flatten",
                                      "cullgraph"]})

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
    with open("test_simple_pe/build/problem.txt", "w") as f:
        f.write(problem)
    assert not os.system(
        "CoSA --problem test_simple_pe/build/problem.txt")


@pytest.mark.parametrize("ops", ops)
def test_simple_pe(ops):
    pe = define_pe(ops, T=m.UInt, data_width=16)

    class SimplePETester(ResetTester, ConfigurationTester):
        pass

    pe_functional_model = gen_simple_pe(ops, 16)()

    tester = SimplePETester(pe, pe.clk, pe_functional_model)

    m.compile("test_simple_pe/build/pe", pe, output="coreir",
              coreir_args={"passes": ["rungenerators", "flatten",
                                      "cullgraph"]})
    # For some reason cullgraph above doesn't result in a culled output,
    # perhaps coreir running it before rungenerators/flatten?
    os.system("coreir -i test_simple_pe/build/pe.json -o test_simple_pe/build/pe.json -p cullgraph")

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
        if i == 0:
            continue
        with open(f"test_simple_pe/build/conf_{op.__name__}.ets", "w") as ets:
            ets.write(f"""\
# INIT
I: self.reset = 0_1
I: self.config_en = 0_1
I: conf_done = 0_1
I: self.config_addr = 0_1
I: self.config_data = 0_{opcode_width}

# STATES


# S0 -> S0a: reset
S0: self.config_addr = 0_1
S0: self.config_data = 0_{opcode_width}
S0: self.config_en = 0_1
S0: self.reset = 0_1
S0: conf_done = 0_1

S0a: self.config_addr = 0_1
S0a: self.config_data = 0_{opcode_width}
S0a: self.config_en = 0_1
S0a: self.reset = 1_1
S0a: conf_done = 0_1

S1: self.config_addr = 0_1
S1: self.config_data = 0_{opcode_width}
S1: self.config_en = 0_1
S1: self.reset = 0_1
S1: conf_done = 0_1

# S1a -> S2a: config
S1a: self.config_addr = 0_1
S1a: self.config_data = {i}_{opcode_width}
S1a: self.config_en = 1_1
S1a: self.reset = 0_1
S1a: conf_done = 0_1

S2: self.config_addr = 0_1
S2: self.config_data = {i}_{opcode_width}
S2: self.config_en = 1_1
S2: self.reset = 0_1
S2: conf_done = 0_1

S2a: self.config_addr = 0_1
S2a: self.config_data = 0_{opcode_width}
S2a: self.config_en = 0_1
S2a: self.reset = 0_1
S2a: conf_done = 1_1

# TRANSITIONS
I -> S0
S0 -> S0a
S0a -> S1
S1 -> S1a
S1a -> S2
S2 -> S2a
S2a -> S2a
""")
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
prove: TRUE
expected: TRUE
"""  # noqa
        with open(f"test_simple_pe/build/problem_{op.__name__}.txt", "w") as f:
            f.write(problem)
        assert not os.system(
            f"CoSA --problem test_simple_pe/build/problem_{op.__name__}.txt -v2")
