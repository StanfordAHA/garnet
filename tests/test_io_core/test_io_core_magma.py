import pytest
from gemstone.common.testers import BasicTester
from gemstone.common.util import compress_config_data
from io_core.io_core_magma import IOCoreValid, IOCore, IOCoreDelay
from fault.tester import Tester
from fault.random import random_bv


@pytest.mark.parametrize("core_type", [IOCore, IOCoreDelay])
def test_regression(run_tb, core_type):
    io_core = core_type()
    io_core.finalize()
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

    run_tb(tester)

@pytest.mark.skip("skipping this test for now since there is a logic bug")
def test_delay_io(run_tb):
    io_core = IOCoreDelay()
    io_core.finalize()

    io_core_circuit = io_core.circuit()
    tester = BasicTester(io_core_circuit, io_core_circuit.clk, io_core_circuit.reset)

    # configure everything to delay mode
    instr = {}
    for width in [1, 16]:
        for prefix in ["glb2io", "io2glb"]:
            reg_name = f"{prefix}_{width}_delay_en"
            instr[reg_name] = 1

    config_data = io_core.get_config_bitstream(instr)
    config_data = compress_config_data(config_data)

    tester.zero_inputs()
    tester.reset()

    for addr, data in config_data:
        tester.configure(addr, data)
        tester.config_read(addr)
        tester.eval()
        tester.expect(io_core_circuit.read_config_data, data)

    for width in [1]:
        vectors = [(random_bv(width), (random_bv(width))) for _ in range(10)]
        for i, (v1, v2) in enumerate(vectors):
            tester.poke(io_core_circuit.glb2io_1, v1)
            tester.poke(io_core_circuit.f2io_1, v2)

            tester.eval()

            if i > 0:
                pre_v1, pre_v2 = vectors[i - 1]
                tester.expect(io_core_circuit.io2f_1, pre_v1)
                tester.expect(io_core_circuit.io2glb_1, pre_v2)

            tester.step(2)

    run_tb(tester, cwd="temp", trace=True)


def test_valid_generation(run_tb):
    io_core = IOCoreValid()
    io_core.finalize()
    io_core_circuit = io_core.circuit()
    tester = BasicTester(io_core_circuit, io_core_circuit.clk, io_core_circuit.reset)

    max_cycle = 16

    # mode set to 1
    # max cycle set to 16
    config_data = [io_core.get_config_data("mode", 1), io_core.get_config_data("max_cycle", max_cycle)]
    config_data = compress_config_data(config_data)

    tester.zero_inputs()
    tester.reset()
    tester.poke(io_core_circuit.stall, 1)

    for addr, data in config_data:
        tester.configure(addr, data)
        tester.config_read(addr)
        tester.eval()
        tester.expect(io_core_circuit.read_config_data, data)

    # un-stall
    tester.poke(io_core_circuit.stall, 0)

    # it should stay low regardless of the IO as long as the reset signal is never high
    for _f2io_16 in [random_bv(16) for _ in range(10)]:
        tester.poke(io_core_circuit.f2io_16, _f2io_16)
        tester.eval()
        tester.expect(io_core_circuit.io2glb_16, _f2io_16)
        tester.expect(io_core_circuit.io2glb_1, 0)

    # hit the start  signal
    tester.poke(io_core_circuit.glb2io_1, 1)
    tester.eval()
    # rising clock edge
    tester.step(2)
    # de-assert the reset/start signal
    tester.poke(io_core_circuit.glb2io_1, 0)
    tester.eval()

    # from now on it should output 1 until it reaches max cycle
    for _ in range(max_cycle):
        tester.expect(io_core_circuit.io2glb_1, 1)
        tester.step(2)

    # then stay low
    for _ in range(max_cycle):
        tester.expect(io_core_circuit.io2glb_1, 0)
        tester.step(2)

    run_tb(tester)
