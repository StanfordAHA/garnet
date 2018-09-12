import pe
from testvectors import complete, random, test_input, test_output
from verilator import testsource, bodysource, run_verilator_test
from collections import OrderedDict
from random import randint, choice
import pytest
import os
import itertools
import inspect
from pe_core import pe_core_genesis2
import glob


def setup_module():
    # Generate the PE
    pe_core_genesis2.pe_core_wrapper.generator()()


def teardown_module():
    # Cleanup PE genesis2 collateral
    for item in glob.glob('genesis_*'):
        os.system(f"rm -r {item}")
    os.system(f"rm PEtest_pe")
    os.system(f"rm PECOMPtest_pe_comp_unq1")
    os.system(f"rm REGMODEtest_opt_reg")
    os.system(f"rm REGMODEtest_opt_reg_file")


ops, signed_ops = [], []
for name, op in inspect.getmembers(pe, inspect.isfunction):
    signature = inspect.signature(op)
    if "signed" in signature.parameters:
        signed_ops.append(name)
        ops.append(name)
    else:
        ops.append(name)


def compile_harness(name, test, body, lut_code, cfg_d, debug_trig=0, debug_trig_p=0):
    harness = f"""\
#include "Vtest_pe.h"
#include "verilated.h"
#include <cassert>
#include <printf.h>

void step(Vtest_pe* top) {{
    top->clk = 0;
    top->eval();
    top->clk = 1;
    top->eval();
}}

void reset(Vtest_pe* top) {{
    top->rst_n = 1;
    top->eval();
    top->rst_n = 0;
    top->eval();
    top->rst_n = 1;
    top->eval();
}}

int main(int argc, char **argv, char **env) {{
    Verilated::commandArgs(argc, argv);
    Vtest_pe* top = new Vtest_pe;

    {test}
    reset(top);
    top->clk_en = 1;

    top->cfg_en = 1;

    top->cfg_d = {lut_code};
    top->cfg_a = 0x00;  // lut_code
    step(top);

    top->cfg_d = 0;
    top->cfg_a = 0xF0;
    step(top);

    top->cfg_d = 0;
    top->cfg_a = 0xF1;
    step(top);

    top->cfg_d = 0;
    top->cfg_a = 0xF3;
    step(top);

    top->cfg_d = 0;
    top->cfg_a = 0xF4;
    step(top);

    top->cfg_d = 0;
    top->cfg_a = 0xF5;
    step(top);

    top->cfg_d = {cfg_d};
    top->cfg_a = 0xFF;  // opcode
    step(top);

    top->cfg_d = {debug_trig};
    top->cfg_a = 0xE0;  // debug_trig
    step(top);

    top->cfg_d = {debug_trig_p};
    top->cfg_a = 0xE1;  // debug_trig_p
    step(top);

    top->cfg_en = 0;

    {body}

    delete top;
    printf("Success!\\n");
    exit(0);
}}
"""
    with open(name, "w") as f:
        f.write(harness)

def pytest_generate_tests(metafunc):
    if 'op' in metafunc.fixturenames:
        metafunc.parametrize("op", ops)
    if 'signed_op' in metafunc.fixturenames:
        metafunc.parametrize("signed_op", signed_ops)
        metafunc.parametrize("signed", [True, False])
    if 'const_value' in metafunc.fixturenames:
        metafunc.parametrize("const_value", range(16))
    if 'signed' in metafunc.fixturenames:
        metafunc.parametrize("signed", [True, False])
    if 'strategy' in metafunc.fixturenames:
        metafunc.parametrize("strategy", [complete, random])

    if 'flag_sel' in metafunc.fixturenames:
        metafunc.parametrize("flag_sel", range(0, 16))

    if 'lut_code' in metafunc.fixturenames:
        metafunc.parametrize("lut_code", range(0, 16))

    if 'random_op' in metafunc.fixturenames:
        metafunc.parametrize("random_op", [choice(ops)])

    if 'input_modes' in metafunc.fixturenames:
        input_modes = itertools.product(*(range(0, 4) for _ in range(5)))
        metafunc.parametrize("input_modes", input_modes)

    if 'irq_en_0' in metafunc.fixturenames:
        metafunc.parametrize("irq_en_0", [True, False])
    if 'irq_en_1' in metafunc.fixturenames:
        metafunc.parametrize("irq_en_1", [True, False])
    if 'debug_trig' in metafunc.fixturenames:
        metafunc.parametrize("debug_trig", [0])
    if 'debug_trig_p' in metafunc.fixturenames:
        metafunc.parametrize("debug_trig_p", [0])

def test_op(strategy, op, flag_sel, signed):
    if flag_sel == 0xE:
        return  # Skip lut, tested separately
    if flag_sel in [0x4, 0x5, 0x6, 0x7, 0xA, 0xB, 0xC, 0xD] and not signed:  # Flag modes with N, V are signed only
        return
    if op == "abs" and not signed:
        return  # abs only defined in signed mode
    lut_code = 0x00
    args = [signed] if op in signed_ops else []
    _op = getattr(pe, op)(*args).flag(flag_sel).lut(lut_code).signed(signed)
    cfg_d = _op.instruction

    if strategy is complete:
        width = 4
        N = 1 << width
        tests = complete(_op, OrderedDict([
            ("data0", range(0, N) if not signed else range(- N // 2, N // 2)),
            ("data1", range(0, N) if not signed else range(- N // 2, N // 2)),
            ("bit0", range(0, 2)),
            ("bit1", range(0, 2)),
            ("bit2", range(0, 2)),
        ]), lambda result: (test_output("res", result[0]),
                            test_output("res_p", result[1]),
                            test_output("irq", 1 if result[2] else 0)))
    elif strategy is random:
        n = 16
        width = 16
        N = 1 << width
        tests = random(_op, n, OrderedDict([
            ("data0", lambda : randint(0, N - 1) if not signed else randint(- N // 2, N // 2 - 1)),
            ("data1", lambda : randint(0, N - 1) if not signed else randint(- N // 2, N // 2 - 1)),
            ("bit0", lambda : randint(0, 1)),
            ("bit1", lambda : randint(0, 1)),
            ("bit2", lambda : randint(0, 1))
        ]), lambda result: (test_output("res", result[0]),
                            test_output("res_p", result[1]),
                            test_output("irq", 1 if result[2] else 0)))

    body = bodysource(tests)
    test = testsource(tests)

    build_directory = "test_pe_core/test_pe_old/build"
    compile_harness(f'{build_directory}/harness.cpp', test, body, lut_code, cfg_d)

    run_verilator_test('test_pe', 'harness', 'test_pe', build_directory)

def test_input_modes(signed, input_modes):
    op = "add"
    lut_code = randint(0, 15)
    flag_sel = randint(0, 15)
    if not signed:
        # Skip flags involving V for unsigned mode
        while flag_sel in [0x6, 0x7, 0xA, 0xB, 0xC, 0xD]:
            flag_sel = randint(0, 15)
    print(f"flag_sel={flag_sel}")
    data0_mode, data1_mode, bit0_mode, bit1_mode, bit2_mode = input_modes
    irq_en = 0
    acc_en = 0
    _op = getattr(pe, op)().flag(flag_sel).lut(lut_code).signed(signed)
    for reg, mode in zip(
        (_op.rega, _op.regb, _op.regd, _op.rege, _op.regf),
        input_modes
    ):
        reg(mode)
    cfg_d = _op.instruction

    strategy = random
    n = 16
    width = 16
    N = 1 << width
    tests = random(_op, n, OrderedDict([
        ("data0", lambda : randint(0, N - 1) if not signed else randint(- N // 2, N // 2 - 1)),
        ("data1", lambda : randint(0, N - 1) if not signed else randint(- N // 2, N // 2 - 1)),
        ("bit0", lambda : randint(0, 1)),
        ("bit1", lambda : randint(0, 1)),
        ("bit2", lambda : randint(0, 1))
    ]), lambda result: (test_output("res", result[0]),
                        test_output("res_p", result[1]),
                        test_output("irq", 1 if result[2] else 0)),
        with_clk=True)

    body = bodysource(tests)
    test = testsource(tests)

    build_directory = "test_pe_core/test_pe_old/build"
    compile_harness(f'{build_directory}/harness.cpp', test, body, lut_code, cfg_d)

    run_verilator_test('test_pe', f'harness', 'test_pe', build_directory)

def test_lut(strategy, signed, lut_code): #, random_op):
    # op = random_op
    # op = choice(ops)
    op = "add"
    flag_sel = 0xE  # Lut output
    bit2_mode = 0x2  # BYPASS
    bit1_mode = 0x2  # BYPASS
    bit0_mode = 0x2  # BYPASS
    data1_mode = 0x2  # BYPASS
    data0_mode = 0x2  # BYPASS
    irq_en = 0
    acc_en = 0
    _op = getattr(pe, op)().flag(flag_sel).lut(lut_code).signed(signed)
    cfg_d = _op.instruction

    if strategy is complete:
        width = 4
        N = 1 << width
        tests = complete(_op, OrderedDict([
            ("data0", range(-1, 1)),  # For now we'll verify that data0/data1
            ("data1", range(-1, 1)),  # don't affect the output
            ("bit0", range(0, 2)),
            ("bit1", range(0, 2)),
            ("bit2", range(0, 2)),
        ]), lambda result: (test_output("res", result[0]),
                            test_output("res_p", result[1]),
                            test_output("irq", 1 if result[2] else 0)))
    elif strategy is random:
        return # We just test the LUT completely

    body = bodysource(tests)
    test = testsource(tests)

    build_directory = "test_pe_core/test_pe_old/build"
    compile_harness(f'{build_directory}/harness.cpp', test, body, lut_code, cfg_d)

    run_verilator_test('test_pe', 'harness', 'test_pe', build_directory)

def test_irq(strategy, irq_en_0, irq_en_1, debug_trig, debug_trig_p, signed):
    op = "add"
    flag_sel = 0x0  # Z
    lut_code = 0x0
    acc_en = 0
    _op = getattr(pe, op)().flag(flag_sel).lut(lut_code).irq_en(irq_en_0, irq_en_1).signed(signed)
    cfg_d = _op.instruction

    if strategy is complete:
        width = 4
        N = 1 << width
        tests = complete(_op, OrderedDict([
            ("data0", range(-1, 1)),  # For now we'll verify that data0/data1
            ("data1", range(-1, 1)),  # don't affect the output
            ("bit0", range(0, 2)),
            ("bit1", range(0, 2)),
            ("bit2", range(0, 2)),
        ]), lambda result: (test_output("res", result[0]),
                            test_output("res_p", result[1]),
                            test_output("irq", 1 if result[2] else 0)))
    elif strategy is random:
        return # We just test the LUT completely

    body = bodysource(tests)
    test = testsource(tests)

    build_directory = "test_pe_core/test_pe_old/build"
    compile_harness(f'{build_directory}/harness.cpp', test, body, lut_code, cfg_d, debug_trig, debug_trig_p)

    run_verilator_test('test_pe', 'harness', 'test_pe', build_directory)
