import glob
import pytest
import pe
import fault
import os
from random import randint
import inspect
from pe_core import pe_core_genesis2
import glob
import itertools
import magma as m

# Generate the PE
pe_core = pe_core_genesis2.pe_core_wrapper.generator()()
pe_compute_unit = m.DefineFromVerilogFile(
    'genesis_verif/test_pe_comp_unq1.sv')[0]
_tester = fault.Tester(pe_compute_unit)
_tester.compile(target='verilator', directory="test_pe_core/build",
                include_directories=["../../genesis_verif"],
                magma_output="verilog",
                flags=['-Wno-fatal'])


@pytest.fixture
def tester(scope="module"):
    return _tester


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
        metafunc.parametrize("strategy", ["complete", "random"])


build_dir = "test_pe_core/build"


def run_test(functional_model, strategy, tester, signed):
    tester.clear()
    pe_compute_unit = tester.circuit
    N = 4
    _iter = None
    if strategy == "complete":
        _iter = itertools.product(range(0, N), range(0, N), range(0, 2))
    elif strategy == "random":
        n = 256
        _iter = [
            (randint(0, (1 << N) - 1), randint(0, (1 << N) - 1), randint(0, 1))
            for _ in range(n)
        ]
    tester.poke(pe_compute_unit.op_code, functional_model.instruction)
    for op_a, op_b, op_d_p in _iter:
        tester.poke(pe_compute_unit.op_a, op_a)
        tester.poke(pe_compute_unit.op_b, op_b)
        tester.poke(pe_compute_unit.op_d_p, op_d_p)
        tester.eval()
        res, res_p = functional_model._alu(op_a=op_a, op_b=op_b, op_d_p=op_d_p)
        tester.expect(pe_compute_unit.res, res)
        tester.expect(pe_compute_unit.res_p, res_p)
        tester.eval()
    tester.run(target='verilator')


def test_op(op, strategy, tester):
    functional_model = getattr(pe, op)()
    run_test(functional_model, strategy, tester, False)


def test_signed_op(signed_op, signed, strategy, tester):
    functional_model = getattr(pe, signed_op)(signed)
    run_test(functional_model, strategy, tester, signed)
