import pytest
from bit_vector import BitVector
import magma as m
from simple_cb.simple_cb_magma import CB
from simple_cb.simple_cb import gen_simple_cb
from simple_cb.simple_cb_genesis2 import simple_cb_wrapper
from common.testers import ResetTester, ConfigurationTester
from fault.random import random_bv
from fault import Tester


@pytest.mark.parametrize('num_tracks', [10])
def test_regression(num_tracks):
    params = {
        "width": 16,
        "num_tracks": num_tracks,
    }

    # Create magma circuit.
    magma_simple_cb = CB(**params).circuit()
    m.compile(f"test_simple_cb/build/{magma_simple_cb.name}", magma_simple_cb,
              output="coreir-verilog")

    simple_cb_functional_model = gen_simple_cb(**params)()

    tester = Tester(magma_simple_cb, magma_simple_cb.clk)

    def reset():
        simple_cb_functional_model.reset()
        tester.poke(magma_simple_cb.reset, 1)
        tester.eval()
        tester.poke(magma_simple_cb.reset, 0)

    def configure(addr, data):
        simple_cb_functional_model.configure(BitVector(addr.as_uint(), 32), data)
        tester.poke(magma_simple_cb.clk, 0)
        tester.poke(magma_simple_cb.reset, 0)
        tester.poke(magma_simple_cb.config.config_addr, addr)
        tester.poke(magma_simple_cb.config.config_data, data)
        # tester.poke(magma_simple_cb.config.write, 1)
        tester.step(2)

    for config_data in [BitVector(x, 32) for x in range(num_tracks)]:
        reset()
        configure(BitVector(0, 8), config_data)
        inputs = [random_bv(16) for _ in range(num_tracks)]
        for i, input_ in enumerate(inputs):
            tester.poke(magma_simple_cb.I[i], input_)
        tester.eval()
        tester.expect(magma_simple_cb.O, inputs[config_data.as_uint()])

    tester.compile_and_run(target="verilator",
                           skip_compile=True,
                           directory="test_simple_cb/build",
                           flags=["-Wno-fatal"])
