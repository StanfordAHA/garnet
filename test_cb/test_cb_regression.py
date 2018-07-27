import shutil
import os
import glob
from bit_vector import BitVector

from cb.cb_magma import define_cb
from cb.cb import gen_cb
from cb.cb_genesis2 import cb_wrapper

import magma as m

import pytest

from fault.test_vector_generator import generate_test_vectors_from_streams
from fault.functional_tester import FunctionalTester
from fault.random import random_bv


def teardown_function():
    for item in glob.glob('genesis_*'):
        os.system(f"rm -r {item}")


@pytest.mark.parametrize('default_value,has_constant',
                         # Test 10 random default values with has_constant
                         [(random_bv(16), 1) for _ in range(2)] +
                         # include one test with no constant
                         [(random_bv(16), 0)])
# FIXME: this fails
# @pytest.mark.parametrize('num_tracks', range(2,10))
@pytest.mark.parametrize('num_tracks', [10])
def test_regression(default_value, num_tracks, has_constant):
    feedthrough_outputs = "1111101111"
    params = {
        "width": 16,
        "num_tracks": num_tracks,
        "feedthrough_outputs": feedthrough_outputs,
        "has_constant": has_constant,
        "default_value": default_value.as_int()
    }

    magma_cb = define_cb(**params)
    m.compile(f"test_cb/build/{magma_cb.name}", magma_cb,
              output="coreir-verilog")

    genesis_cb = cb_wrapper.generator()(
        **params, input_files=["cb/genesis/cb.vp"])
    genesis_verilog = "genesis_verif/cb.v"
    shutil.copy(genesis_verilog, "test_cb/build")

    def get_inputs_and_data_width(circuit):
        data_width = None

        inputs = []
        for port in circuit.interface:
            if port[:3] == "in_":
                inputs.append(port)
                port_width = len(circuit.interface.ports[port])
                if data_width is None:
                    data_width = port_width
                else:
                    assert data_width == port_width
        return inputs, data_width

    inputs, data_width = get_inputs_and_data_width(genesis_cb)

    assert (inputs, data_width) == get_inputs_and_data_width(magma_cb), \
        "Inputs should be the same"

    config_addr = BitVector(0, 32)

    cb_functional_model = gen_cb(**params)()
    tester = FunctionalTester(genesis_cb, genesis_cb.clk, cb_functional_model)
    for config_data in [BitVector(x, 32) for x in range(0, len(inputs))]:
        # TODO: Do we need this extra instantiation, could the function do it
        # for us?
        tester.poke(genesis_cb.reset, 1)
        tester.eval()

        # init inputs to 0
        for i in range(0, num_tracks):
            if feedthrough_outputs[i] == "1":
                tester.poke(getattr(genesis_cb, f"in_{i}"), 0)
        tester.poke(genesis_cb.clk, 0)
        tester.poke(genesis_cb.reset, 0)
        tester.poke(genesis_cb.config_addr, config_addr)
        tester.poke(genesis_cb.config_data, config_data)
        tester.poke(genesis_cb.config_en, 1)

        tester.step()

        # posedge of clock, so cb should now be configured
        cb_functional_model.configure(config_addr, config_data)

        tester.step()
        tester.expect(genesis_cb.read_data, cb_functional_model.read_data)
        tester.test_vectors += \
            generate_test_vectors_from_streams(
                # Interesting example of Python's dynamic scoping, observe how
                # the following code is incorrect because of when the string
                # argument to getattr is evaluated
                # genesis_cb, cb_functional_model, dict(**{
                #   f"in_{i}": lambda name, port: random_bv(
                #     len(getattr(genesis_cb, f"in_i{i}")))
                #   for i in range(num_tracks) if feedthrough_outputs[i] == "1"
                # }, **{
                genesis_cb, cb_functional_model, dict(**{
                    f"in_{i}": lambda name, port: random_bv(
                        len(port))
                    for i in range(num_tracks) if feedthrough_outputs[i] == "1"
                }, **{
                    "clk": 0,
                    "reset": 0,
                    "config_addr": 0,
                    "config_data": 0,
                    "config_en": 0
                }))

    for cb in [genesis_cb, magma_cb]:
        tester.circuit = cb
        tester.compile_and_run(directory="test_cb/build", target="verilator",
                               flags=["-Wno-fatal"])
