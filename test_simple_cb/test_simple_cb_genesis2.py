from simple_cb import simple_cb_genesis2
import glob
import os


def teardown_function():
    for item in glob.glob('genesis_*'):
        os.system(f"rm -r {item}")


def test_simple_cb_genesis2(capsys):
    parser = simple_cb_genesis2.create_parser()
    args = parser.parse_args([
        "--width", "16",
        "--num_tracks", "10",
        "simple_cb/genesis/simple_cb.vp"
    ])

    simple_cb_genesis2.main(args)
    out, _ = capsys.readouterr()
    assert out == f"""\
Running genesis cmd 'Genesis2.pl -parse -generate -top simple_cb -input simple_cb/genesis/simple_cb.vp -parameter simple_cb.width='16' -parameter simple_cb.num_tracks='10''
simple_cb(clk: In(Bit), reset: In(Bit), in_0: Array(16,In(Bit)), in_1: Array(16,In(Bit)), in_2: Array(16,In(Bit)), in_3: Array(16,In(Bit)), in_4: Array(16,In(Bit)), in_5: Array(16,In(Bit)), in_6: Array(16,In(Bit)), in_7: Array(16,In(Bit)), in_8: Array(16,In(Bit)), in_9: Array(16,In(Bit)), out: Array(16,Out(Bit)), config_addr: Array(32,In(Bit)), config_data: Array(32,In(Bit)), config_en: In(Bit), read_data: Array(32,Out(Bit)))
"""  # nopep8
