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
        "--cfg_op_width", "5"
    ]
    global_controller_genesis2.gc_wrapper.main(argv=argv)
    out, _ = capsys.readouterr()
    assert out == f"""\
Running genesis cmd 'Genesis2.pl -parse -generate -top global_controller -input global_controller/genesis/global_controller.vp global_controller/genesis/jtag.vp global_controller/genesis/tap.vp global_controller/genesis/flop.vp global_controller/genesis/cfg_and_dbg.vp -parameter global_controller.cfg_bus_width='32' -parameter global_controller.cfg_addr_width='32' -parameter global_controller.cfg_op_width='5''
global_controller(clk_in: In(Bit), reset_in: In(Bit), config_data_in: In(Bits(32)), config_addr_out: Out(Bits(32)), config_data_out: Out(Bits(32)), clk_out: Out(Bit), reset_out: Out(Bit), cgra_stalled: Out(Bits(4)), read: Out(Bit), write: Out(Bit), tdi: In(Bit), tdo: Out(Bit), tms: In(Bit), tck: In(Bit), trst_n: In(Bit))
"""  # nopep8
