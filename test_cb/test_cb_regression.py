import shutil
import os
import glob
from bit_vector import BitVector

from cb.cb_magma import define_cb
from cb.cb import gen_cb
from cb.cb_genesis2 import cb_wrapper

import magma as m

import pytest

from fault.action_generators import generate_actions_from_streams
from common.testers import ResetTester, ConfigurationTester
from common.regression_test import check_interfaces
from fault.random import random_bv


def teardown_function():
    for item in glob.glob('genesis_*'):
        os.system(f"rm -r {item}")


@pytest.mark.skip("Blocked by https://github.com/rdaly525/coreir/issues/627")
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
        "default_value": default_value.as_uint()
    }

    magma_cb = define_cb(**params)
    m.compile(f"test_cb/build/{magma_cb.name}", magma_cb,
              output="coreir-verilog")

    genesis_cb = cb_wrapper.generator()(
        **params, input_files=["cb/genesis/cb.vp"])
    genesis_verilog = "genesis_verif/cb.v"

    check_interfaces(magma_cb, genesis_cb)
    shutil.copy(genesis_verilog, "test_cb/build")

    config_addr = BitVector(0, 32)

    cb_functional_model = gen_cb(**params)()

    class CBTester(ResetTester, ConfigurationTester):
        pass

    tester = CBTester(genesis_cb, genesis_cb.clk, cb_functional_model)
    for config_data in [BitVector(x, 32) for x in range(0, num_tracks)]:
        tester.zero_inputs()
        tester.reset()
        tester.configure(config_addr, config_data)

        tester.actions += \
            generate_actions_from_streams(
                # Interesting example of Python's dynamic scoping, observe how
                # the following code is incorrect because of when the string
                # argument to getattr is evaluated
                # genesis_cb, cb_functional_model, dict(**{
                #   f"in_{i}": lambda name, port: random_bv(
                #     len(getattr(genesis_cb, f"in_i{i}")))
                #   for i in range(num_tracks) if feedthrough_outputs[i] == "1"
                # }, **{
                genesis_cb, cb_functional_model, {
                    f"in_{i}": lambda name, port: random_bv(
                        len(port))
                    for i in range(num_tracks) if feedthrough_outputs[i] == "1"
                })

    for cb, output in [(genesis_cb, "verilog"), (magma_cb, "coreir-verilog")]:
        name = cb.name
        if cb == "magma_cb":
            name = "global_" + cb.name
        tester.retarget(cb, cb.clk) \
              .compile_and_run(circuit_name=name,
                               directory="test_cb/build", target="verilator",
                               flags=["-Wno-fatal"], magma_output=output)
