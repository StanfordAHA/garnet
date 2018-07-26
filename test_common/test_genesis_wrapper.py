import pytest
import inspect
import random
import magma as m
from common.genesis_wrapper import GenesisWrapper
from common.generator_interface import GeneratorInterface


TOP = "test_run_genesis"
INFILES = ["test_common/test_run_genesis.vp"]
PARAMS = {
    "width": 16,
}
INTERFACE = GeneratorInterface()\
            .register("width", int, 32)
WRAPPER = GenesisWrapper(INTERFACE, TOP, INFILES)


def test_generator():
    def _foo(*args, **kwargs):
        pass
    generator = WRAPPER.generator()
    assert inspect.isfunction(generator)
    assert inspect.signature(generator) == inspect.signature(_foo)
    module = generator(**PARAMS)
    assert isinstance(module, m.circuit.DefineCircuitKind)
    expected_ports = {
        "clk" : m.Out(m.Bit),
        "reset" : m.Out(m.Bit),
        "in0" : m.Array(16, m.Out(m.Bit)),
        "in1" : m.Array(16, m.Out(m.Bit)),
        "sel" : m.Out(m.Bit),
        "out" : m.Array(16, m.In(m.Bit)),
    }
    for name, type_ in module.interface.ports.items():
        assert expected_ports[name] == type(type_)


def test_parser_basic():
    parser = WRAPPER.parser()
    w = random.randint(0, 100)
    infiles = ["/path/to/file.vp", "/some/otherfile.vp"]
    argv = ["--width", str(w)] + infiles
    args = parser.parse_args(argv)
    assert len(vars(args)) == 2
    assert args.width == w
    assert args.infiles == infiles


def test_parser_default():
    parser = WRAPPER.parser()
    args = parser.parse_args([])
    assert len(vars(args)) == 2
    assert args.width == INTERFACE.params["width"][1]
    assert args.infiles == INFILES


def test_parser_error():
    parser = WRAPPER.parser()
    with pytest.raises(SystemExit) as pytest_e:
        args = parser.parse_args(["--bad_arg", "0"])
        assert False
    assert pytest_e.type == SystemExit
    assert pytest_e.value.code == 2


def test_main(capsys):
    w = random.randint(0, 100)
    WRAPPER.main(argv=["--width", str(w)])
    out, _ = capsys.readouterr()
    expected_out = f"""\
Running genesis cmd 'Genesis2.pl -parse -generate -top test_run_genesis -input {''.join(INFILES)} -parameter test_run_genesis.width='{w}''
test_run_genesis(clk: In(Bit), reset: In(Bit), in0: Array({w},In(Bit)), in1: Array({w},In(Bit)), sel: In(Bit), out: Array({w},Out(Bit)))
"""  # nopep8
    assert out == expected_out
