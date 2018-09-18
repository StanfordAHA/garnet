from pe_core import pe_core_genesis2
import glob
import os
import shutil
import fault
import random
from bit_vector import BitVector
from common.testers import ResetTester, ConfigurationTester
import pytest


def teardown_function():
    for item in glob.glob('genesis_*'):
        os.system(f"rm -r {item}")
    os.system(f"rm PEtest_pe")
    os.system(f"rm PECOMPtest_pe_comp_unq1")
    os.system(f"rm REGMODEtest_opt_reg")
    os.system(f"rm REGMODEtest_opt_reg_file")


def test_main(capsys):
    argv = [
        "pe_core/genesis/test_pe_red.svp",
        "pe_core/genesis/test_pe_dual.vpf",
        "pe_core/genesis/test_pe_comp.svp",
        "pe_core/genesis/test_pe_comp_dual.svp",
        "pe_core/genesis/test_cmpr.svp",
        "pe_core/genesis/test_pe.svp",
        "pe_core/genesis/test_mult_add.svp",
        "pe_core/genesis/test_full_add.svp",
        "pe_core/genesis/test_lut.svp",
        "pe_core/genesis/test_opt_reg.svp",
        "pe_core/genesis/test_simple_shift.svp",
        "pe_core/genesis/test_shifter.svp",
        "pe_core/genesis/test_debug_reg.svp",
        "pe_core/genesis/test_opt_reg_file.svp"
    ]
    pe_core_genesis2.pe_core_wrapper.main(argv=argv)
    out, _ = capsys.readouterr()
    assert out == f"""\
Running genesis cmd 'Genesis2.pl -parse -generate -top test_pe -input pe_core/genesis/test_pe_red.svp pe_core/genesis/test_pe_dual.vpf pe_core/genesis/test_pe_comp.svp pe_core/genesis/test_pe_comp_dual.svp pe_core/genesis/test_cmpr.svp pe_core/genesis/test_pe.svp pe_core/genesis/test_mult_add.svp pe_core/genesis/test_full_add.svp pe_core/genesis/test_lut.svp pe_core/genesis/test_opt_reg.svp pe_core/genesis/test_simple_shift.svp pe_core/genesis/test_shifter.svp pe_core/genesis/test_debug_reg.svp pe_core/genesis/test_opt_reg_file.svp -parameter test_pe.reg_inputs='1' -parameter test_pe.reg_out='0' -parameter test_pe.use_add='2' -parameter test_pe.use_cntr='1' -parameter test_pe.use_bool='1' -parameter test_pe.use_shift='1' -parameter test_pe.mult_mode='2' -parameter test_pe.use_div='0' -parameter test_pe.is_msb='0' -parameter test_pe.en_double='0' -parameter test_pe.en_opt='1' -parameter test_pe.en_trick='0' -parameter test_pe.use_abs='1' -parameter test_pe.use_max_min='1' -parameter test_pe.use_relu='0' -parameter test_pe.get_carry='1' -parameter test_pe.debug='0' -parameter test_pe.use_flip='0' -parameter test_pe.use_acc='1' -parameter test_pe.en_ovfl='1' -parameter test_pe.en_debug='1' -parameter test_pe.lut_inps='3' -parameter test_pe.reg_cnt='1''
test_pe(clk: in(clock), rst_n: in(bit), clk_en: in(bit), cfg_d: in(bits(32)), cfg_a: in(bits(8)), cfg_en: in(bit), data0: in(bits(16)), data1: in(bits(16)), data2: in(bits(16)), bit0: in(bit), bit1: in(bit), bit2: in(bit), res: out(bits(16)), irq: out(bit), res_p: out(bit), read_data: out(bits(32)))
"""  # nopep8


@pytest.mark.skip("Incomplete")
def test_pe_core():
    generator = pe_core_genesis2.pe_wrapper.generator()
    PECore = generator()  # Using default params
    for genesis_verilog in glob.glob("genesis_verif/*.v"):
        shutil.copy(genesis_verilog, "test_pe_core/build")
