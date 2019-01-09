from io1bit import io1bit_genesis2
import glob
import os


def teardown_function():
    for item in glob.glob('genesis_*'):
        os.system(f"rm -r {item}")
    os.system(f"rm TILEio1bit")


def test_main(capsys):
    argv = [
        "io1bit/genesis/io1bit.vp"
    ]
    io1bit_genesis2.io1bit_wrapper.main(argv=argv)
    out, _ = capsys.readouterr()
    assert out == f"""\
Running genesis cmd 'Genesis2.pl -parse -generate -top io1bit -input io1bit/genesis/io1bit.vp -parameter io1bit.io_group='0' -parameter io1bit.side='0''
io1bit(clk: In(Clock), reset: In(AsyncReset), pad: InOut(Bit), p2f: Out(Bit), f2p_16: In(Bit), f2p_1: In(Bit), config_addr: In(Bits(32)), config_data: In(Bits(32)), config_write: In(Bit), config_read: In(Bit), tile_id: In(Bits(16)), read_data: Out(Bits(32)))
"""  # nopep8
