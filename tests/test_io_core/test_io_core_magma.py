import tempfile
from hwtypes import BitVector
from io_core.io_core_magma import IOCore
from fault.tester import Tester
from fault.random import random_bv


def test_regression():
    io_core = IOCore()
    io_core_circuit = io_core.circuit()
    tester = Tester(io_core_circuit)

    for _glb2io_16, _f2io_16 in \
            [(random_bv(16), random_bv(16)) for _ in range(100)]:
        tester.poke(io_core_circuit.glb2io_16, _glb2io_16)
        tester.poke(io_core_circuit.f2io_16, _f2io_16)
        tester.eval()
        tester.expect(io_core_circuit.io2glb_16, _f2io_16)
        tester.expect(io_core_circuit.io2f_16, _glb2io_16)

    for _glb2io_1, _f2io_1 in \
            [(random_bv(1), random_bv(1)) for _ in range(100)]:
        tester.poke(io_core_circuit.glb2io_1, _glb2io_1)
        tester.poke(io_core_circuit.f2io_1, _f2io_1)
        tester.eval()
        tester.expect(io_core_circuit.io2glb_1, _f2io_1)
        tester.expect(io_core_circuit.io2f_1, _glb2io_1)

    with tempfile.TemporaryDirectory() as tempdir:
        tester.compile_and_run(target="verilator",
                               magma_output="coreir-verilog",
                               directory=tempdir,
                               flags=["-Wno-fatal"])
