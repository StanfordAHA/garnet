import pytest
from random import randint
import tempfile
from bit_vector import BitVector
import fault
import fault.random
import magma
from common.mux_interface import MuxInterface
from common.mux_wrapper import MuxWrapper
from common.aoi_mux import AOIMux


def mux_interface_helper(height, width, mux_class):
    """
    Test that a class @mux_class which implements the MuxInterface class works
    as expected. Specifically, we initialize a mux with random height and width,
    and check that the output is as expected for select in range [0, height).

    Note that we do not check the behavior with sel >= height, because this is
    undefined behavior.
    """
    mux = mux_class(height, width)
    assert isinstance(mux, MuxInterface)
    assert mux.height == height
    assert mux.width == width
    assert mux.name() == f"MuxWrapper_{height}_{width}"

    mux_circuit = mux.circuit()
    tester = fault.Tester(mux_circuit)
    inputs = [fault.random.random_bv(width) for _ in range(height)]
    for i, input_ in enumerate(inputs):
        tester.poke(mux_circuit.I[i], input_)
    for i in range(height):
        tester.poke(mux_circuit.S, BitVector(i, mux.sel_bits))
        tester.eval()
        tester.expect(mux_circuit.O, inputs[i])
    with tempfile.TemporaryDirectory() as tempdir:
        tester.compile_and_run(directory=tempdir,
                               magma_output="coreir-verilog",
                               flags=["-Wno-fatal"])


@pytest.mark.parametrize('height,width', [(randint(2, 10), randint(1, 32))
                                          for _ in range(5)])
def test_mux_wrapper(height, width):
    mux_interface_helper(height, width, MuxWrapper)


@pytest.mark.parametrize('height,width', [(randint(2, 10), randint(1, 32))
                                          for _ in range(5)])
def test_aoi_mux(height, width):
    mux_interface_helper(height, width, AOIMux)
