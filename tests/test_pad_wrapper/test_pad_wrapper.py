import pytest
from random import randint
import tempfile
from hwtypes import BitVector
import fault
import fault.random
import magma
from pad_wrapper.pad_wrapper import Pad


@pytest.mark.parametrize('is_input,is_vertical',
                         [(0, 0), (0, 1), (1, 0), (1, 1)])
def test_mux_wrapper(is_input, is_vertical):
    pad = Pad(is_input, is_vertical)

    pad_circuit = pad.circuit()
    tester = fault.Tester(pad_circuit)

    if is_input:
        input_port = pad_circuit.pad
        output_port = pad_circuit.fabric
    else:
        input_port = pad_circuit.fabric
        output_port = pad_circuit.pad

    for input_ in range(2):
        tester.poke(input_port, BitVector[1](input_))
        tester.eval()
        tester.expect(output_port, input_)

    tester.compile_and_run(directory="tests/test_pad_wrapper/build",
                           magma_output="coreir-verilog",
                           target="verilator",
                           flags=["-Wno-fatal"])
