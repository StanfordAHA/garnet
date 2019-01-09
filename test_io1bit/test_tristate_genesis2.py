from io1bit import tristate_genesis2
import glob
import os


def teardown_function():
    for item in glob.glob('genesis_*'):
        os.system(f"rm -r {item}")


def test_main(capsys):
    argv = [
        "io1bit/genesis/tristate.vp"
    ]
    tristate_genesis2.tristate_wrapper.main(argv=argv)
    out, _ = capsys.readouterr()
    assert out == f"""\
Running genesis cmd 'Genesis2.pl -parse -generate -top tristate -input io1bit/genesis/tristate.vp '
tristate(io_bit: In(Bit), out_bus: In(Bit), f2p_16: In(Bit), f2p_1: In(Bit), pad: InOut(Bit))
"""  # nopep8
