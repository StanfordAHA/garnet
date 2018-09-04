from bit_vector import BitVector
from simple_pe.simple_pe_magma import define_pe
from simple_pe.simple_pe import gen_simple_pe
from common.testers import ResetTester, ConfigurationTester
from fault.test_vector_generator import generate_test_vectors_from_streams
from fault.random import random_bv
import operator
import magma as m
import mantle
import os


def test_simple_pe():
    ops = [operator.add, operator.sub, operator.and_, operator.or_]
    pe = define_pe(ops, T=m.UInt, data_width=16)

    class SimplePETester(ResetTester, ConfigurationTester):
        pass

    pe_functional_model = gen_simple_pe(ops, 16)()

    tester = SimplePETester(pe, pe.clk, pe_functional_model)

    m.compile("test_simple_pe/build/pe", pe, output="coreir",
              coreir_args={"passes": ["rungenerators", "flatten",
                                      "cullgraph"]})

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
bmc_length: 30
verification: safety

[PE check {op.__name__}]
description: "Check configuring to opcode={i} corresponds to {op.__name__}"
formula: (conf_done = 1_1) -> ((self.I0 {op_strs[op]} self.I1) = self.O)
prove: TRUE
expected: TRUE
"""  # noqa
        with open(f"test_simple_pe/build/problem_{op.__name__}.txt", "w") as f:
            f.write(problem)
        assert not os.system(
            f"CoSA --problem test_simple_pe/build/problem_{op.__name__}.txt")
