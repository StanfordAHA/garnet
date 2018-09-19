import pytest
import random
import tempfile
import fault
from common.zext_wrapper import ZextWrapper


@pytest.mark.parametrize("in_width,out_width", [(5, 10), (10, 5)])
def test_zext_wrapper(in_width, out_width):
    if in_width >= out_width:
        with pytest.raises(ValueError) as pytest_e:
            ZextWrapper(in_width, out_width)
            assert False
        expected_error = ValueError(f"output width must be greater than input "
                                    f"width (output width = {out_width}, input "
                                    f"width = {in_width})")
        assert pytest_e.type == type(expected_error)
        assert repr(pytest_e.value) == repr(expected_error)
        return

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
