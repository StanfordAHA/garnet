from sb import sb_genesis2
import glob
import os


def teardown_function():
    for item in glob.glob('genesis_*'):
        os.system(f"rm -r {item}")


def test_sb_genesis2(capsys):
    argv = [
        "--width", "16",
        "--num_tracks", "2",
        "--sides", "4",
        "--feedthrough_outputs", "00",
        "--registered_outputs", "11",
        "--pe_output_count", "1",
        "--is_bidi", "0",
        "--sb_fs", "10#10#10",
        "sb/genesis/sb.vp"
    ]
    sb_genesis2.sb_wrapper.main(argv=argv)
    out, _ = capsys.readouterr()
    assert out == f"""\
Running genesis cmd 'Genesis2.pl -parse -generate -top sb -input sb/genesis/sb.vp -parameter sb.width='16' -parameter sb.num_tracks='2' -parameter sb.sides='4' -parameter sb.feedthrough_outputs='00' -parameter sb.registered_outputs='11' -parameter sb.pe_output_count='1' -parameter sb.is_bidi='0' -parameter sb.sb_fs='10#10#10''
sb(clk: In(Bit), clk_en: In(Bit), reset: In(Bit), pe_output_0: In(Bits(16)), out_0_0: Out(Bits(16)), in_0_0: In(Bits(16)), out_0_1: Out(Bits(16)), in_0_1: In(Bits(16)), out_1_0: Out(Bits(16)), in_1_0: In(Bits(16)), out_1_1: Out(Bits(16)), in_1_1: In(Bits(16)), out_2_0: Out(Bits(16)), in_2_0: In(Bits(16)), out_2_1: Out(Bits(16)), in_2_1: In(Bits(16)), out_3_0: Out(Bits(16)), in_3_0: In(Bits(16)), out_3_1: Out(Bits(16)), in_3_1: In(Bits(16)), config_addr: In(Bits(32)), config_data: In(Bits(32)), config_en: In(Bit), read_data: Out(Bits(32)))
"""  # nopep8
