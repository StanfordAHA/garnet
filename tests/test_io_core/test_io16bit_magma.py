import tempfile
from hwtypes import BitVector
from io_core.io16bit_magma import IO16bit
from fault.tester import Tester
from fault.random import random_bv


def test_regression():
    io16bit = IO16bit()
    io16bit_circuit = io16bit.circuit()
    tester = Tester(io16bit_circuit)

    for _glb2io, _f2io in [(random_bv(16), random_bv(16)) for _ in range(100)]:
        tester.poke(io16bit_circuit.glb2io, _glb2io)
        tester.poke(io16bit_circuit.f2io_16, _f2io)
        tester.eval()
        tester.expect(io16bit_circuit.io2glb, _f2io)
        tester.expect(io16bit_circuit.io2f_16, _glb2io)

    with tempfile.TemporaryDirectory() as tempdir:
        tester.compile_and_run(target="verilator",
                               magma_output="coreir-verilog",
                               directory=tempdir,
                               flags=["-Wno-fatal"])
