import pytest
from random import randint, choice
import tempfile
from bit_vector import BitVector
import fault
import fault.random
import magma
from common.mux_with_default import MuxWithDefaultWrapper


test_cases = [(randint(2, 10), randint(1, 32), randint(4, 32),
               randint(0, 100)) for _ in range(5)]
test_cases += [(10, 16, 3, 0)]


@pytest.mark.parametrize('num_inputs,width,sel_bits,default', test_cases)
def test_mux_with_default_wrapper(num_inputs, width, sel_bits, default):
    if 2 ** sel_bits <= num_inputs:
        with pytest.raises(ValueError) as pytest_e:
            MuxWithDefaultWrapper(num_inputs, width, sel_bits, default)
            assert False
        expected_error = ValueError(f"(2 ^ sel_bits) must be > num_inputs "
                                    f"(sel_bits={sel_bits}, "
                                    f"num_inputs={num_inputs})")
        assert pytest_e.type == type(expected_error)
        assert repr(pytest_e.value) == repr(expected_error)
        return
    mux = MuxWithDefaultWrapper(num_inputs, width, sel_bits, default)
    assert mux.num_inputs == num_inputs
    assert mux.width == width
    assert mux.sel_bits == sel_bits
    assert mux.default == default
    assert mux.name() == f"MuxWithDefaultWrapper_{num_inputs}_{width}"\
        f"_{sel_bits}_{default}"

    mux_circuit = mux.circuit()
    tester = fault.Tester(mux_circuit)
    inputs = [fault.random.random_bv(width) for _ in range(num_inputs)]
    for i, input_ in enumerate(inputs):
        tester.poke(mux_circuit.I[i], input_)
    tester.poke(mux_circuit.EN, 1)
    for i in range(num_inputs):
        tester.poke(mux_circuit.S, BitVector(i, mux.sel_bits))
        tester.eval()
        tester.expect(mux_circuit.O, inputs[i])
    for _ in range(10):
        sel = choice(range(num_inputs, 2 ** sel_bits))
        tester.poke(mux_circuit.S, BitVector(sel, mux.sel_bits))
        tester.eval()
        tester.expect(mux_circuit.O, default)
    # Test that with EN=0, we get the default value, even with select being in
    # [0, num_inputs).
    tester.poke(mux_circuit.EN, 0)
    for i in range(num_inputs):
        tester.poke(mux_circuit.S, BitVector(i, mux.sel_bits))
        tester.eval()
        tester.expect(mux_circuit.O, default)
    with tempfile.TemporaryDirectory() as tempdir:
        tester.compile_and_run(directory=tempdir,
                               magma_output="coreir-verilog",
                               flags=["-Wno-fatal"])
