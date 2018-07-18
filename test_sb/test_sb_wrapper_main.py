from sb import sb_wrapper_main
import glob
import os


def teardown_function():
#   for item in glob.glob('genesis_*'):
#        os.system(f"rm -r {item}")
     pass

def test_sb_wrapper(capsys):
    parser = sb_wrapper_main.create_parser()
    args = parser.parse_args([
        "--width", "16",
        "--num_tracks", "2",
        "--sides", "4",
        "--feedthrough_outputs", "00",
        "--registered_outputs", "11",
        "--pe_output_count", "1",
        "--is_bidi", "0",
        "--sb_fs", "10#10#10",
        "test_sb/sb.vp"
    ])

    sb_wrapper_main.main(args)
    out, _ = capsys.readouterr()
    assert out == f"""\
Running genesis cmd 'Genesis2.pl -parse -generate -top sb -input test_sb/sb.vp -parameter sb.width='16' -parameter sb.num_tracks='2' -parameter sb.sides='4' -parameter sb.feedthrough_outputs='00' -parameter sb.registered_outputs='11' -parameter sb.pe_output_count='1' -parameter sb.is_bidi='0' -parameter sb.sb_fs='10#10#10''
sb(clk: In(Bit), clk_en: In(Bit), reset: In(Bit), pe_output_0: Array(16,In(Bit)), out_0_0: Array(16,Out(Bit)), in_0_0: Array(16,In(Bit)), out_0_1: Array(16,Out(Bit)), in_0_1: Array(16,In(Bit)), out_1_0: Array(16,Out(Bit)), in_1_0: Array(16,In(Bit)), out_1_1: Array(16,Out(Bit)), in_1_1: Array(16,In(Bit)), out_2_0: Array(16,Out(Bit)), in_2_0: Array(16,In(Bit)), out_2_1: Array(16,Out(Bit)), in_2_1: Array(16,In(Bit)), out_3_0: Array(16,Out(Bit)), in_3_0: Array(16,In(Bit)), out_3_1: Array(16,Out(Bit)), in_3_1: Array(16,In(Bit)), config_addr: Array(32,In(Bit)), config_data: Array(32,In(Bit)), config_en: In(Bit), read_data: Array(32,Out(Bit)))
"""  # nopep8
