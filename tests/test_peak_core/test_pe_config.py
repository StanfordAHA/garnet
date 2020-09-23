from gemstone.common.testers import BasicTester
from gemstone.common.run_verilog_sim import irun_available
from peak_core.peak_core import PeakCore

from peak.family import PyFamily
from lassen.sim import PE_fc
from lassen.asm import (add, Mode_t, lut_and, inst, ALU_t,
                        umult0, fp_mul, fp_add,
                        fcnvexp2f, fcnvsint2f, fcnvuint2f)
from lassen.common import BFloat16_fc
import hwtypes
import shutil
import tempfile
import os
import pytest


@pytest.fixture(scope="module")
def dw_files():
    filenames = ["DW_fp_add.v", "DW_fp_mult.v"]
    dirname = "peak_core"
    result_filenames = []
    for name in filenames:
        filename = os.path.join(dirname, name)
        assert os.path.isfile(filename)
        result_filenames.append(filename)
    return result_filenames


@pytest.mark.skip(reason="Hacky registers are no longer needed")
def test_pe_config(dw_files):
    core = PeakCore(PE_fc)
    core.name = lambda: "PECore"
    circuit = core.circuit()

    # random test stuff
    tester = BasicTester(circuit, circuit.clk, circuit.reset)
    tester.reset()

    tester.poke(circuit.interface["stall"], 1)
    config_data = core.get_config_bitstream(add(ra_mode=Mode_t.DELAY,
                                                rb_mode=Mode_t.DELAY))
    # hacky way to configure it as 0x42 + 0x42 from the operand register
    config_data += [(3, 0x42 << 16 | 0x42)]
    for addr, data in config_data:
        print("{0:08X} {1:08X}".format(addr, data))
        tester.configure(addr, data)
        tester.config_read(addr)
        tester.eval()
        tester.expect(circuit.read_config_data, data)

    for i in range(10):
        tester.poke(circuit.interface["data0"], i + 1)
        tester.poke(circuit.interface["data1"], i + 1)
        tester.eval()
        tester.expect(circuit.interface["alu_res"], 0x42 + 0x42)

    tester.reset()
    lut_val = lut_and().lut

    config_data = core.get_config_bitstream(inst(alu=ALU_t.Add, lut=lut_val,
                                                 rd_mode=Mode_t.DELAY,
                                                 re_mode=Mode_t.DELAY,
                                                 rf_mode=Mode_t.DELAY))
    config_data += [(4, 0x7)]
    tester.poke(circuit.interface["bit0"], 0)
    tester.poke(circuit.interface["bit1"], 0)
    tester.eval()
    tester.expect(circuit.interface["res_p"], 1)

    with tempfile.TemporaryDirectory() as tempdir:
        for filename in dw_files:
            shutil.copy(filename, tempdir)
        tester.compile_and_run(target="verilator",
                               magma_output="coreir-verilog",
                               magma_opts={"coreir_libs": {"float_DW"}},
                               directory=tempdir,
                               flags=["-Wno-fatal"])


def _make_random(cls):
    if issubclass(cls, hwtypes.BitVector):
        return cls.random(len(cls))
    if issubclass(cls, hwtypes.FPVector):
        while True:
            val = cls.random()
            if val.fp_is_normal():
                return val.reinterpret_as_bv()
    return NotImplemented


_CAD_DIR = "/cad/synopsys/syn/P-2019.03/dw/sim_ver/"
_EXPENSIVE = {
    "bits32.mul": ((umult0(),), "magma_Bits_32_mul_inst0", hwtypes.UIntVector[16]),  # noqa
    "bfloat16.mul": ((fp_mul(),), "magma_BFloat_16_mul_inst0", BFloat16_fc(PyFamily())),  # noqa
    "bfloat16.add": ((fp_add(),), "magma_BFloat_16_add_inst0", BFloat16_fc(PyFamily())),  # noqa
}


@pytest.mark.parametrize("op", list(_EXPENSIVE.keys()))
def test_pe_data_gate(op, dw_files):
    instrs, fu, BV = _EXPENSIVE[op]

    is_float = issubclass(BV, hwtypes.FPVector)
    if not irun_available() and is_float:
        pytest.skip("Need irun to test fp ops")

    core = PeakCore(PE_fc)
    core.name = lambda: "PECore"
    circuit = core.circuit()

    tester = BasicTester(circuit, circuit.clk, circuit.reset)

    alu = tester.circuit.WrappedPE_inst0.PE_inst0.ALU_inst0.ALU_comb_inst0
    fu = getattr(alu, fu)
    other_fu = set(_EXPENSIVE[other_op][1]
                   for other_op in _EXPENSIVE
                   if other_op != op)
    other_fu = [getattr(alu, k) for k in other_fu]

    def _test_instr(instr):
        # Configure PE.
        tester.reset()
        config_data = core.get_config_bitstream(instr)
        for addr, data in config_data:
            tester.configure(addr, data)
        # Stream data.
        for _ in range(100):
            a = _make_random(BV)
            b = _make_random(BV)
            tester.poke(circuit.data0, a)
            tester.poke(circuit.data1, b)
            tester.eval()
            expected, _, _ = core.wrapper.model(instr, a, b)
            tester.expect(circuit.alu_res, expected)
            for other_fu_i in other_fu:
                tester.expect(other_fu_i.I0, 0)
                tester.expect(other_fu_i.I1, 0)

    for instr in instrs:
        _test_instr(instr)

    with tempfile.TemporaryDirectory() as tempdir:
        if is_float:
            assert os.path.isdir(_CAD_DIR)
            ext_srcs = list(map(os.path.basename, dw_files))
            ext_srcs += ["DW_fp_addsub.v"]
            ext_srcs = [os.path.join(_CAD_DIR, src) for src in ext_srcs]
            tester.compile_and_run(target="system-verilog",
                                   simulator="ncsim",
                                   magma_output="coreir-verilog",
                                   ext_srcs=ext_srcs,
                                   magma_opts={"coreir_libs": {"float_DW"}},
                                   directory=tempdir,)
        else:
            for filename in dw_files:
                shutil.copy(filename, tempdir)
            tester.compile_and_run(target="verilator",
                                   magma_output="coreir-verilog",
                                   magma_opts={"coreir_libs": {"float_DW"},
                                               "verilator_debug": True},
                                   directory=tempdir,
                                   flags=["-Wno-fatal"])
