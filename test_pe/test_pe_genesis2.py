from pe import pe_genesis2
import glob
import os
import shutil
import fault
import random
from bit_vector import BitVector
from common.testers import ResetTester, ConfigurationTester


def teardown_function():
    for item in glob.glob('genesis_*'):
        os.system(f"rm -r {item}")
    os.system(f"rm PEtest_pe")


def test_main(capsys):
    argv = [
        "pe/genesis/test_pe_red.svp",
        "pe/genesis/test_pe_dual.vpf",
        "pe/genesis/test_pe_comp.svp",
        "pe/genesis/test_pe_comp_dual.svp",
        "pe/genesis/test_cmpr.svp",
        "pe/genesis/test_pe.svp",
        "pe/genesis/test_mult_add.svp",
        "pe/genesis/test_full_add.svp",
        "pe/genesis/test_lut.svp",
        "pe/genesis/test_opt_reg.svp",
        "pe/genesis/test_simple_shift.svp",
        "pe/genesis/test_shifter.svp",
        "pe/genesis/test_debug_reg.svp",
        "pe/genesis/test_opt_reg_file.svp"
    ]
    pe_genesis2.pe_wrapper.main(argv=argv)
    out, _ = capsys.readouterr()
    assert out == f"""\
Running genesis cmd 'Genesis2.pl -parse -generate -top test_pe -input pe/genesis/test_pe_red.svp pe/genesis/test_pe_dual.vpf pe/genesis/test_pe_comp.svp pe/genesis/test_pe_comp_dual.svp pe/genesis/test_cmpr.svp pe/genesis/test_pe.svp pe/genesis/test_mult_add.svp pe/genesis/test_full_add.svp pe/genesis/test_lut.svp pe/genesis/test_opt_reg.svp pe/genesis/test_simple_shift.svp pe/genesis/test_shifter.svp pe/genesis/test_debug_reg.svp pe/genesis/test_opt_reg_file.svp -parameter test_pe.reg_inputs='1' -parameter test_pe.reg_out='0' -parameter test_pe.use_add='2' -parameter test_pe.use_cntr='1' -parameter test_pe.use_bool='1' -parameter test_pe.use_shift='1' -parameter test_pe.mult_mode='2' -parameter test_pe.use_div='0' -parameter test_pe.is_msb='0' -parameter test_pe.en_double='0' -parameter test_pe.en_opt='1' -parameter test_pe.en_trick='0' -parameter test_pe.use_abs='1' -parameter test_pe.use_max_min='1' -parameter test_pe.use_relu='0' -parameter test_pe.get_carry='1' -parameter test_pe.debug='0' -parameter test_pe.use_flip='0' -parameter test_pe.use_acc='1' -parameter test_pe.en_ovfl='1' -parameter test_pe.en_debug='1' -parameter test_pe.lut_inps='3' -parameter test_pe.reg_cnt='1''
test_pe(clk: In(Bit), rst_n: In(Bit), clk_en: In(Bit), cfg_d: Array(32,In(Bit)), cfg_a: Array(8,In(Bit)), cfg_en: In(Bit), data0: Array(16,In(Bit)), data1: Array(16,In(Bit)), data2: Array(16,In(Bit)), bit0: In(Bit), bit1: In(Bit), bit2: In(Bit), res: Array(16,Out(Bit)), irq: Out(Bit), res_p: Out(Bit), read_data: Array(32,Out(Bit)))
"""  # nopep8


def test_pe():
    generator = pe_genesis2.pe_wrapper.generator()
    PE = generator()  # Using default params
    for genesis_verilog in glob.glob("genesis_verif/*.v"):
        shutil.copy(genesis_verilog, "test_pe/build")
