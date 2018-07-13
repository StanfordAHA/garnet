from cb import cb_wrapper_main
import glob
import os


def teardown_function():
    for item in glob.glob('genesis_*'):
        os.system(f"rm -r {item}")


def test_cb_wrapper(capsys):
    parser = cb_wrapper_main.create_parser()
    args = parser.parse_args([
        "--width", "16",
        "--num_tracks", "10",
        "--feedthrough_outputs", "1111101111",
        "--has_constant", "1",
        "--default_value", "7",
        "test_cb/cb.vp"
    ])

    cb_wrapper_main.main(args)
    out, _ = capsys.readouterr()
    assert out == f"""\
Running genesis cmd 'Genesis2.pl -parse -generate -top cb -input test_cb/cb.vp -parameter cb.width='16' -parameter cb.num_tracks='10' -parameter cb.feedthrough_outputs='1111101111' -parameter cb.has_constant='1' -parameter cb.default_value='7''
cb(clk: In(Bit), reset: In(Bit), in_0: Array(16,In(Bit)), in_1: Array(16,In(Bit)), in_2: Array(16,In(Bit)), in_3: Array(16,In(Bit)), in_4: Array(16,In(Bit)), in_6: Array(16,In(Bit)), in_7: Array(16,In(Bit)), in_8: Array(16,In(Bit)), in_9: Array(16,In(Bit)), out: Array(16,Out(Bit)), config_addr: Array(32,In(Bit)), config_data: Array(32,In(Bit)), config_en: In(Bit), read_data: Array(32,Out(Bit)))
"""  # nopep8
