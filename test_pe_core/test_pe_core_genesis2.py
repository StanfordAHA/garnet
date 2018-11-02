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
Running genesis cmd 'Genesis2.pl -parse -generate -top test_pe -input pe_core/genesis/test_pe_red.svp pe_core/genesis/test_pe_dual.vpf pe_core/genesis/test_pe_comp.svp pe_core/genesis/test_pe_comp_dual.svp pe_core/genesis/test_cmpr.svp pe_core/genesis/test_pe.svp pe_core/genesis/test_mult_add.svp pe_core/genesis/test_full_add.svp pe_core/genesis/test_lut.svp pe_core/genesis/test_opt_reg.svp pe_core/genesis/test_simple_shift.svp pe_core/genesis/test_shifter.svp pe_core/genesis/test_debug_reg.svp pe_core/genesis/test_opt_reg_file.svp -parameter test_pe.reg_inputs='1' -parameter test_pe.reg_out='0' -parameter test_pe.use_add='1' -parameter test_pe.use_cntr='0' -parameter test_pe.use_bool='1' -parameter test_pe.use_shift='1' -parameter test_pe.mult_mode='1' -parameter test_pe.use_div='0' -parameter test_pe.is_msb='0' -parameter test_pe.en_double='0' -parameter test_pe.en_opt='1' -parameter test_pe.en_trick='0' -parameter test_pe.use_abs='1' -parameter test_pe.use_max_min='1' -parameter test_pe.use_relu='0' -parameter test_pe.get_carry='1' -parameter test_pe.debug='0' -parameter test_pe.use_flip='0' -parameter test_pe.use_acc='1' -parameter test_pe.en_ovfl='1' -parameter test_pe.en_debug='1' -parameter test_pe.lut_inps='3' -parameter test_pe.reg_cnt='1''
test_pe(clk: In(Clock), rst_n: In(AsyncReset), clk_en: In(Bit), cfg_d: In(Bits(32)), cfg_a: In(Bits(8)), cfg_en: In(Bit), data0: In(Bits(16)), data1: In(Bits(16)), bit0: In(Bit), bit1: In(Bit), bit2: In(Bit), res: Out(Bits(16)), irq: Out(Bit), res_p: Out(Bit), read_data: Out(Bits(32)))
"""  # nopep8
