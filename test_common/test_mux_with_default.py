import pytest
from random import randint, choice
import tempfile
from bit_vector import BitVector
import fault
import fault.random
import magma
from common.mux_with_default import MuxWithDefaultWrapper


@pytest.mark.parametrize('num_inputs,width,sel_bits,default',
                         [(randint(2, 10), randint(1, 32), randint(4, 32),
                           randint(0, 100)) for _ in range(5)])
def test_mux_with_default_wrapper(num_inputs, width, sel_bits, default):
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
    with tempfile.TemporaryDirectory() as tempdir:
        tester.compile_and_run(directory=tempdir,
                               magma_output="coreir-verilog",
                               flags=["-Wno-fatal"])
