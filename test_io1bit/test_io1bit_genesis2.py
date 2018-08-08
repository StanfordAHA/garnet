from io1bit import io1bit_genesis2
import glob
import os


def teardown_function():
    for item in glob.glob('genesis_*'):
        os.system(f"rm -r {item}")


def test_io1bit_genesis2(capsys):
    parser = io1bit_genesis2.create_parser()
    args = parser.parse_args([
        "--io_group", "0",
        "--side", "0",
        "io1bit/genesis/io1bit.vp"
    ])
    io1bit_genesis2.main(args)
    out, _ = capsys.readouterr()
    assert out == f"""\
Running genesis cmd 'Genesis2.pl -parse -generate -top io1bit -input io1bit/genesis/io1bit.vp -parameter io1bit.io_group='0' -parameter io1bit.side='0''
io1bit(clk: In(Bit), reset: In(Bit), pad: Bit, p2f: Out(Bit), f2p_16: In(Bit), f2p_1: In(Bit), config_addr: Array(32,In(Bit)), config_data: Array(32,In(Bit)), config_write: In(Bit), config_read: In(Bit), tile_id: Array(16,In(Bit)), read_data: Array(32,Out(Bit)))
"""  # nopep8
