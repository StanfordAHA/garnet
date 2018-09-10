import pytest
import subprocess
import pe
from testvectors import complete, random, test_output
from verilator import compile, run_verilator_test
import ncsim
import delegator
import os
from random import randint
from collections import OrderedDict
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

def run_ncsim_test(op, opcode, tests, strategy):
    return
    if os.environ.get("TRAVIS", True):
        # Skip on Travis because cadence tools not available
        # FIXME: Should check for cadence tools available instead
        return
    ncsim.compile(f'test_{op}_{strategy.__name__}', opcode, tests)
    RTL_FOLDER = "../../hardware/generator_z/top/genesis_verif"
    result = delegator.run(f"""
irun -top test_pe_comp_unq1_tb -timescale 1ns/1ps -l irun.log -access +rwc -notimingchecks -input ../../hardware/generator_z/impl/verif/cmd.tcl build/ncsim_test_{op}_{strategy.__name__}_tb.v /nobackup/nikhil3/arm_mems/arm/tsmc/cln40g/sram_sp_hsc_rvt_hvt_rvt/r10p2/sram_512w_16b/sram_512w_16b.v {RTL_FOLDER}/cb_unq1.v {RTL_FOLDER}/cb_unq2.v {RTL_FOLDER}/cb_unq3.v {RTL_FOLDER}/global_signal_tile_unq1.v {RTL_FOLDER}/io1bit_unq1.v {RTL_FOLDER}/io1bit_unq2.v {RTL_FOLDER}/io1bit_unq3.v {RTL_FOLDER}/io1bit_unq4.v {RTL_FOLDER}/jtag_unq1.sv {RTL_FOLDER}/memory_core_unq1.v {RTL_FOLDER}/memory_tile_unq1.v {RTL_FOLDER}/mem_unq1.v {RTL_FOLDER}/pe_tile_new_unq1.v {RTL_FOLDER}/sb_unq1.v {RTL_FOLDER}/sb_unq2.v {RTL_FOLDER}/sb_unq3.v  {RTL_FOLDER}/test_cmpr.sv {RTL_FOLDER}/test_full_add.sv {RTL_FOLDER}/test_lut.sv {RTL_FOLDER}/test_mult_add.sv {RTL_FOLDER}/test_opt_reg.sv {RTL_FOLDER}/test_pe_comp_unq1.sv {RTL_FOLDER}/test_pe_unq1.sv {RTL_FOLDER}/test_shifter_unq1.sv {RTL_FOLDER}/top.v
    """)
    assert not result.return_code, result.out + "\n" + result.err
    assert "Failed!" not in result.out, result.out + "\n" + result.err

ops, signed_ops = [], []
for name, op in inspect.getmembers(pe, inspect.isfunction):
    signature = inspect.signature(op)
    if "signed" in signature.parameters:
        signed_ops.append(name)
    else:
        ops.append(name)

def pytest_generate_tests(metafunc):
    if 'op' in metafunc.fixturenames:
        metafunc.parametrize("op", ops)
    if 'signed_op' in metafunc.fixturenames:
        metafunc.parametrize("signed_op", signed_ops)
        metafunc.parametrize("signed", [True, False])
    if 'const_value' in metafunc.fixturenames:
        metafunc.parametrize("const_value", range(16))
    if 'strategy' in metafunc.fixturenames:
        metafunc.parametrize("strategy", [complete, random])

@pytest.fixture
def worker_id(request):
    if hasattr(request.config, 'slaveinput'):
        return request.config.slaveinput['slaveid']
    else:
        return 'master'


def get_tests(pe, strategy, signed=False):
    if strategy is complete:
        width = 4
        N = 1 << width
        tests = complete(pe._alu, OrderedDict([
            ("op_a", range(0, N - 1) if not signed else range(- N // 2, N // 2)),
            ("op_b", range(0, N - 1) if not signed else range(- N // 2, N // 2)),
            ("op_d_p", range(0, 2))
        ]), lambda result: (test_output("res", result[0]), test_output("res_p", result[1])))
    elif strategy is random:
        n = 256
        width = 16
        N = 1 << width
        tests = random(pe._alu, n, OrderedDict([
            ("op_a", lambda : randint(0, N - 1) if not signed else randint(- N // 2, N // 2 - 1)),
            ("op_b", lambda : randint(0, N - 1) if not signed else randint(- N // 2, N // 2 - 1)),
            ("op_d_p", lambda : randint(0, 1))
        ]), lambda result: (test_output("res", result[0]), test_output("res_p", result[1])))
    else:
        raise NotImplementedError()
    return tests


build_dir = "test_pe_core/test_pe_old/build"


def test_op(op, strategy):
    a = getattr(pe, op)()

    tests = get_tests(a, strategy)

    compile('harness', 'test_pe_comp_unq1', a.instruction , tests,
            build_dir=build_dir)
    run_verilator_test('test_pe_comp_unq1', 'harness', 'test_pe_comp_unq1',
                       build_dir=build_dir)
    # run_ncsim_test(op, a.instruction, tests, strategy)

def test_signed_op(signed_op, signed, strategy):
    a = getattr(pe, signed_op)(signed)

    tests = get_tests(a, strategy, signed)

    compile('harness', 'test_pe_comp_unq1', a.instruction, tests,
            build_dir=build_dir)
    run_verilator_test('test_pe_comp_unq1', 'harness', 'test_pe_comp_unq1',
                       build_dir=build_dir)
    # run_ncsim_test(signed_op, a.instruction, tests, strategy)
