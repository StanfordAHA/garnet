import pytest
import tempfile
from bit_vector import BitVector
import fault, fault.random
from simple_cb.simple_cb_magma import CB


@pytest.mark.parametrize('num_tracks', [2, 5, 10])
def test_regression(num_tracks):
    params = {
        "width": 16,
        "num_tracks": num_tracks,
    }

    # Create magma circuit.
    simple_cb = CB(**params)

    # TODO(rsetaluri): Check some basic properties of this generator.

    simple_cb_circuit = simple_cb.circuit()
    tester = fault.Tester(simple_cb_circuit, simple_cb_circuit.clk)

    def reset():
        tester.poke(simple_cb_circuit.reset, 1)
        tester.eval()
        tester.poke(simple_cb_circuit.reset, 0)

    # TODO(rsetaluri): Instead of these custom reset(), configure(), and
    # config_read() methods, use the ResetTester and ConfigTester in
    # garnet. This also requires bringing in the functional model that exists in
    # simple_cb/simple_cb.py (see test_simple_cb/test_simple_cb_regression.py).

    def configure(addr, data):
        tester.poke(simple_cb_circuit.clk, 0)
        tester.poke(simple_cb_circuit.reset, 0)
        tester.poke(simple_cb_circuit.config.config_addr, addr)
        tester.poke(simple_cb_circuit.config.config_data, data)
        tester.poke(simple_cb_circuit.config.read, 0)
        # TODO(alexcarsello): Once config.write logic is enabled, check that
        # leaving write=0 does not perform a reconfiguration.
        #tester.poke(simple_cb_circuit.config.write, 1)
        tester.step(2)

    def config_read(addr):
        tester.poke(simple_cb_circuit.clk, 0)
        tester.poke(simple_cb_circuit.reset, 0)
        tester.poke(simple_cb_circuit.config.config_addr, addr)
        tester.poke(simple_cb_circuit.config.read, 1)
        tester.poke(simple_cb_circuit.config.write, 0)
        tester.step(2)

    for config_data in [BitVector(x, 32) for x in range(num_tracks)]:
        reset()
        configure(BitVector(0, 8), config_data)
        config_read(BitVector(0, 8))
        tester.eval()
        tester.expect(simple_cb_circuit.read_config_data, config_data)
        inputs = [fault.random.random_bv(16) for _ in range(num_tracks)]
        for i, input_ in enumerate(inputs):
            tester.poke(simple_cb_circuit.I[i], input_)
        tester.eval()
        tester.expect(simple_cb_circuit.O, inputs[config_data.as_uint()])

    with tempfile.TemporaryDirectory() as tempdir:
        tester.compile_and_run(target="verilator",
                               magma_output="coreir-verilog",
                               directory=tempdir,
                               flags=["-Wno-fatal"])
