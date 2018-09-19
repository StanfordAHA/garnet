import random
import tempfile
import fault
from common.zext_wrapper import ZextWrapper


def test_zext_wrapper():
    in_width = 10
    out_width = 15

    zext_wrapper = ZextWrapper(in_width, out_width)

    assert zext_wrapper.in_width == in_width
    assert zext_wrapper.out_width == out_width

    zext_wrapper_circuit = zext_wrapper.circuit()

    tester = fault.Tester(zext_wrapper_circuit)
    for _ in range(10):
        value = random.randint(0, 2 ** in_width - 1)
        tester.poke(zext_wrapper_circuit.I, value)
        tester.eval()
        tester.expect(zext_wrapper_circuit.O, value)
    with tempfile.TemporaryDirectory() as tempdir:
        tester.compile_and_run(target="verilator",
                               directory=tempdir,
                               magma_output="coreir-verilog")
