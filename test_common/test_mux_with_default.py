import pytest
from random import randint
import tempfile
from bit_vector import BitVector
import fault
import fault.random
import magma
from common.mux_with_default import MuxWithDefaultWrapper


@pytest.mark.parametrize('height,width,default',
                         [(randint(2, 10), randint(1, 32), 1)
                          for _ in range(5)])
def test_mux_with_default_wrapper(height, width, default):
    mux = MuxWithDefaultWrapper(height, width, default)
    assert mux.height == height
    assert mux.width == width
    assert mux.default == default
    assert mux.name() == f"MuxWithDefaultWrapper_{height}_{width}_{default}"

    mux_circuit = mux.circuit()
    tester = fault.Tester(mux_circuit)
    inputs = [fault.random.random_bv(width) for _ in range(height)]
    for i, input_ in enumerate(inputs):
        tester.poke(mux_circuit.I[i], input_)
    tester.poke(mux_circuit.EN, 1)
    sel_bits = mux.sel_bits
    for i in range(2 ** sel_bits):
        tester.poke(mux_circuit.S, BitVector(i, mux.sel_bits))
        tester.eval()
        if i < height:
           tester.expect(mux_circuit.O, inputs[i])
        else:
           tester.expect(mux_circuit.O, default)
    with tempfile.TemporaryDirectory() as tempdir:
        tester.compile_and_run(directory=tempdir,
                               magma_output="coreir-verilog",
                               flags=["-Wno-fatal"])
