from global_controller import global_controller_genesis2
import glob
import os


def teardown_function():
    for item in glob.glob('genesis_*'):
        os.system(f"rm -r {item}")


def test_global_controller_genesis2(capsys):
    argv = [
        "--cfg_bus_width", "32",
        "--cfg_addr_width", "32",
        "--cfg_op_width", "5",
        "--num_analog_regs", "15"
    ]
    global_controller_genesis2.gc_wrapper.main(argv=argv)
    out, _ = capsys.readouterr()
    assert out == f"""\
Running genesis cmd 'Genesis2.pl -parse -generate -top global_controller -input global_controller/genesis/global_controller.vp global_controller/genesis/jtag.vp global_controller/genesis/analog_regfile.vp global_controller/genesis/tap.vp global_controller/genesis/flop.vp global_controller/genesis/cfg_and_dbg.vp -parameter global_controller.cfg_bus_width='32' -parameter global_controller.cfg_addr_width='32' -parameter global_controller.cfg_op_width='5' -parameter global_controller.num_analog_regs='15''
global_controller(clk_in: In(Bit), reset_in: In(Bit), analog_r0: Array(32,Out(Bit)), analog_r1: Array(32,Out(Bit)), analog_r2: Array(32,Out(Bit)), analog_r3: Array(32,Out(Bit)), analog_r4: Array(32,Out(Bit)), analog_r5: Array(32,Out(Bit)), analog_r6: Array(32,Out(Bit)), analog_r7: Array(32,Out(Bit)), analog_r8: Array(32,Out(Bit)), analog_r9: Array(32,Out(Bit)), analog_r10: Array(32,Out(Bit)), analog_r11: Array(32,Out(Bit)), analog_r12: Array(32,Out(Bit)), analog_r13: Array(32,Out(Bit)), analog_r14: Array(32,Out(Bit)), config_data_in: Array(32,In(Bit)), config_addr_out: Array(32,Out(Bit)), config_data_out: Array(32,Out(Bit)), clk_out: Out(Bit), reset_out: Out(Bit), cgra_stalled: Array(4,Out(Bit)), read: Out(Bit), write: Out(Bit), tdi: In(Bit), tdo: Out(Bit), tms: In(Bit), tck: In(Bit), trst_n: In(Bit), jm_out: Array(20,In(Bit)))
"""  # nopep8
