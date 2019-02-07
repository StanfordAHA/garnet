import tempfile
from bit_vector import BitVector

from io_core.io16bit_magma import IO16bit
from fault.tester import Tester

import pytest

def test_regression():
    io16bit = IO16bit()
    io16bit_circuit = io16bit.circuit()
    tester = Tester(io16bit_circuit)

    for _glb2io in [BitVector(x, 1) for x in range(2**16)]:
        for _f2io in [BitVector(x, 1) for x in range(2**16)]:
            tester.poke(io16bit_circuit.glb2io, _glb2io)
            tester.poke(io16bit_circuit.f2io, _f2io)
            tester.eval()
            tester.expect(io16bit_circuit.io2glb, _f2io)
            tester.expect(io16bit_circuit.io2f, _glb2io)

    with tempfile.TemporaryDirectory() as tempdir:
        tester.compile_and_run(target="verilator",
                               magma_output="coreir-verilog",
                               directory=tempdir,
                               flags=["-Wno-fatal"])

