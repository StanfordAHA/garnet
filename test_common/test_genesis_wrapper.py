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


@pytest.mark.parametrize("mode", ["declare", "define"])
def test_generator(mode):
    def _foo(*args, **kwargs):
        pass
    generator = WRAPPER.generator(mode=mode)
    assert inspect.isfunction(generator)
    assert inspect.signature(generator) == inspect.signature(_foo)
    # Check that passing non-kwargs fails.
    try:
        generator(0)
        assert False
    except NotImplementedError as e:
        pass
    module = generator(**PARAMS)
    type_ = m.circuit.DefineCircuitKind if mode == "define" \
        else m.circuit.CircuitKind
    assert isinstance(module, type_)
    expected_ports = {
        "clk": m.Out(m.Bit),
        "reset": m.Out(m.Bit),
        "in0": m.Out(m.Bits(16)),
        "in1": m.Out(m.Bits(16)),
        "sel": m.Out(m.Bit),
        "out": m.In(m.Bits(16)),
    }
    for name, type_ in module.IO.ports.items():
        assert type(expected_ports[name]) == type(type_)


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
test_run_genesis(clk: In(Bit), reset: In(Bit), in0: In(Bits({w})), in1: In(Bits({w})), sel: In(Bit), out: Out(Bits({w})))
"""  # nopep8
    assert out == expected_out
