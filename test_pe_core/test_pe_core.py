import pe
from random import randint, choice
import pytest
import os
import itertools
import inspect
from pe_core import pe_core_genesis2
import glob
import fault


# PECore uses it's own tester rather than a functional tester because the pe.py
# functional model doesn't match the new garnet functional model interface.
# Once we have a new functional model, we can migrate this tester to use the
# Testers in common.testers
class PECoreTester(fault.Tester):
    def reset(self):
        self.poke(self.circuit.rst_n, 1)
        self.eval()
        self.poke(self.circuit.rst_n, 0)
        self.eval()
        self.poke(self.circuit.rst_n, 1)
        self.eval()

    def configure(self, lut_code, cfg_d, debug_trig=0, debug_trig_p=0):
        self.poke(self.circuit.cfg_en, 1)

        # TODO: Get these addresses from the PECore generator
        self.poke(self.circuit.cfg_d, lut_code)
        self.poke(self.circuit.cfg_a, 0x00)
        self.step(2)

        # TODO: Why did we set these addresses to 0?
        self.poke(self.circuit.cfg_d, 0)
        self.poke(self.circuit.cfg_a, 0xF0)
        self.step(2)

        self.poke(self.circuit.cfg_d, 0)
        self.poke(self.circuit.cfg_a, 0xF1)
        self.step(2)

        self.poke(self.circuit.cfg_d, 0)
        self.poke(self.circuit.cfg_a, 0xF3)
        self.step(2)

        self.poke(self.circuit.cfg_d, 0)
        self.poke(self.circuit.cfg_a, 0xF4)
        self.step(2)

        self.poke(self.circuit.cfg_d, 0)
        self.poke(self.circuit.cfg_a, 0xF5)
        self.step(2)

        self.poke(self.circuit.cfg_d, cfg_d)
        self.poke(self.circuit.cfg_a, 0xFF)
        self.step(2)

        self.poke(self.circuit.cfg_d, debug_trig)
        self.poke(self.circuit.cfg_a, 0xE0)
        self.step(2)

        self.poke(self.circuit.cfg_d, debug_trig_p)
        self.poke(self.circuit.cfg_a, 0xE1)
        self.step(2)

        self.poke(self.circuit.cfg_en, 0)
        self.step(2)


@pytest.fixture(scope="module")
def tester():
    # Generate the PE
    pe_core = pe_core_genesis2.pe_core_wrapper.generator()()
    _tester = PECoreTester(pe_core, pe_core.clk)
    _tester.compile(target='verilator', directory="test_pe_core/build",
                    include_directories=["../../genesis_verif"],
                    magma_output="verilog",
                    flags=['-Wno-fatal'])
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
        ops.append(name)
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
    if 'signed' in metafunc.fixturenames:
        metafunc.parametrize("signed", [True, False])
    if 'strategy' in metafunc.fixturenames:
        if metafunc.config.option.longrun:
            metafunc.parametrize("strategy", ["complete", "random"])
        else:
            metafunc.parametrize("strategy", ["random"])

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
        metafunc.parametrize("debug_trig", [randint(0, (1 << 16) - 1)])
    if 'debug_trig_p' in metafunc.fixturenames:
        metafunc.parametrize("debug_trig_p", [randint(0, 1)])


def get_iter(strategy, signed):
    if strategy is "complete":
        width = 4
        N = 1 << width
        return itertools.product(
            range(0, N) if not signed else range(- N // 2, N // 2),  # data0
            range(0, N) if not signed else range(- N // 2, N // 2),  # data1
            range(0, 2),  # bit0
            range(0, 2),  # bit1
            range(0, 2)  # bit2
        )
    elif strategy is "random":
        n = 16
        width = 16
        N = 1 << width
        return [
            (randint(0, N - 1) if not signed else
             randint(- N // 2, N // 2 - 1),  # data0
             randint(0, N - 1) if not signed else
             randint(- N // 2, N // 2 - 1),  # data1
             randint(0, 1),  # bit0
             randint(0, 1),  # bit1
             randint(0, 1))  # bit2
            for _ in range(n)
        ]
    elif strategy is "lut_complete":
        return itertools.product(
            range(0, 2) if not signed else range(-1, 2),  # data0
            range(0, 2) if not signed else range(-1, 2),  # data1
            range(0, 2),  # bit0
            range(0, 2),  # bit1
            range(0, 2)  # bit2
        )
    raise NotImplementedError(strategy)


def run_test(tester, functional_model, strategy, signed, lut_code,
             cfg_d, debug_trig=0, debug_trig_p=0, with_clk=False):
    tester.clear()
    pe_core = tester.circuit
    tester.poke(pe_core.clk_en, 1)
    tester.reset()

    _iter = get_iter(strategy, signed)
    tester.configure(lut_code, cfg_d, debug_trig, debug_trig_p)
    for data0, data1, bit0, bit1, bit2 in _iter:
        tester.poke(pe_core.data0, data0)
        tester.poke(pe_core.data1, data1)
        tester.poke(pe_core.bit0, bit0)
        tester.poke(pe_core.bit1, bit1)
        tester.poke(pe_core.bit2, bit2)
        if not with_clk:
            tester.eval()
            res, res_p, irq = functional_model(data0=data0, data1=data1,
                                               bit0=bit0, bit1=bit1, bit2=bit2)
            tester.expect(pe_core.res, res)
            tester.expect(pe_core.res_p, res_p)
            tester.expect(pe_core.irq, irq)
            tester.eval()
        else:
            for i in range(2):
                tester.step()
                res, res_p, irq = functional_model(data0=data0, data1=data1,
                                                   bit0=bit0, bit1=bit1,
                                                   bit2=bit2, clk=i, clk_en=1)
                tester.expect(pe_core.res, res)
                tester.expect(pe_core.res_p, res_p)
                tester.expect(pe_core.irq, irq)

    tester.run(target='verilator')


@pytest.mark.parametrize('random_flag', [randint(0, 15)])
@pytest.mark.parametrize('random_signed', [randint(0, 1)])
@pytest.mark.parametrize('random_lut_code', [randint(0, 1)])
@pytest.mark.parametrize('random_irq_en', [(randint(0, 1), randint(0, 1))])
@pytest.mark.parametrize('random_debug_trig', [(randint(0, (1 << 16) - 1),
                                                randint(0, 1))])
def test_op_random_quick(op, random_flag, random_signed, tester,
                         random_lut_code, random_irq_en, random_debug_trig):
    irq_en_0, irq_en_1 = random_irq_en
    debug_trig, debug_trig_p = random_debug_trig
    signed = random_signed
    flag_sel = random_flag
    lut_code = random_lut_code
    if flag_sel in [0x4, 0x5, 0x6, 0x7, 0xA, 0xB, 0xC, 0xD] and not signed:
        # Flag modes with N, V are signed only
        signed = True
    if op == "abs":
        # abs only defined in signed mode
        signed = True
    args = [signed] if op in signed_ops else []
    functional_model = getattr(pe, op)(*args).flag(flag_sel)\
                                             .lut(lut_code)\
                                             .irq_en(irq_en_0, irq_en_1)\
                                             .debug_trig(debug_trig)\
                                             .debug_trig_p(debug_trig_p)\
                                             .signed(signed)
    cfg_d = functional_model.instruction
    run_test(tester, functional_model, "random", signed, lut_code, cfg_d,
             debug_trig, debug_trig_p)


def test_op(strategy, op, flag_sel, signed, tester):
    if flag_sel == 0xE:
        return  # Skip lut, tested separately
    if flag_sel in [0x4, 0x5, 0x6, 0x7, 0xA, 0xB, 0xC, 0xD] and not signed:
        # Flag modes with N, V are signed only
        return
    if op == "abs" and not signed:
        return  # abs only defined in signed mode
    lut_code = 0x00
    args = [signed] if op in signed_ops else []
    functional_model = getattr(pe, op)(*args).flag(flag_sel)\
                                             .lut(lut_code)\
                                             .signed(signed)
    cfg_d = functional_model.instruction
    run_test(tester, functional_model, strategy, signed, lut_code, cfg_d)


@pytest.mark.longrun
def test_input_modes(signed, input_modes, tester):
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
    functional_model = getattr(pe, op)().flag(flag_sel)\
                                        .lut(lut_code)\
                                        .signed(signed)
    for reg, mode in zip(
        (functional_model.rega, functional_model.regb, functional_model.regd,
         functional_model.rege, functional_model.regf),
        input_modes
    ):
        reg(mode)
    cfg_d = functional_model.instruction

    run_test(tester, functional_model, "random", signed, lut_code, cfg_d,
             with_clk=True)


def test_lut(signed, lut_code, tester):  # , random_op):
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
    functional_model = getattr(pe, op)().flag(flag_sel)\
                                        .lut(lut_code)\
                                        .signed(signed)
    cfg_d = functional_model.instruction

    run_test(tester, functional_model, "lut_complete", signed, lut_code,
             cfg_d)


def test_irq(strategy, irq_en_0, irq_en_1, debug_trig, debug_trig_p, signed,
             tester):
    op = "add"
    flag_sel = 0x0  # Z
    lut_code = 0x0
    acc_en = 0
    functional_model = getattr(pe, op)().flag(flag_sel)\
                                        .lut(lut_code)\
                                        .irq_en(irq_en_0, irq_en_1)\
                                        .debug_trig(debug_trig)\
                                        .debug_trig_p(debug_trig_p)\
                                        .signed(signed)
    cfg_d = functional_model.instruction

    run_test(tester, functional_model, strategy, signed, lut_code, cfg_d,
             debug_trig, debug_trig_p)
