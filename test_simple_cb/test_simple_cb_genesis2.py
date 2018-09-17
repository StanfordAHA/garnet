from simple_cb import simple_cb_genesis2
import glob
import os


def teardown_function():
    for item in glob.glob('genesis_*'):
        os.system(f"rm -r {item}")


def test_simple_cb_genesis2(capsys):
    argv = [
        "--width", "16",
        "--num_tracks", "10",
        "simple_cb/genesis/simple_cb.vp"
    ]
    simple_cb_genesis2.simple_cb_wrapper.main(argv=argv)
    out, _ = capsys.readouterr()
    assert out == f"""\
Running genesis cmd 'Genesis2.pl -parse -generate -top simple_cb -input simple_cb/genesis/simple_cb.vp -parameter simple_cb.width='16' -parameter simple_cb.num_tracks='10''
simple_cb(clk: In(Clock), reset: In(AsyncReset), in_0: In(Bits(16)), in_1: In(Bits(16)), in_2: In(Bits(16)), in_3: In(Bits(16)), in_4: In(Bits(16)), in_5: In(Bits(16)), in_6: In(Bits(16)), in_7: In(Bits(16)), in_8: In(Bits(16)), in_9: In(Bits(16)), out: Out(Bits(16)), config_addr: In(Bits(32)), config_data: In(Bits(32)), config_en: In(Enable), read_data: Out(Bits(32)))
"""  # nopep8
