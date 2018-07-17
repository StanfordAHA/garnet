import random
import shutil
import os
import glob
from bit_vector import BitVector

from simple_cb.simple_cb_magma import define_simple_cb
from simple_cb.simple_cb import gen_simple_cb
from simple_cb.simple_cb_genesis2 import define_simple_cb_wrapper

import magma as m
import fault
from magma.testing.verilator import compile, run_verilator_test
from common.util import compile_to_verilog

import pytest


def teardown_function():
    for item in glob.glob('genesis_*'):
        os.system(f"rm -r {item}")


def random_bv(width):
    return BitVector(random.randint(0, (1 << width) - 1), width)

def parse_genesis_circuit(circuit):
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


# FIXME: this fails
# @pytest.mark.parametrize('num_tracks', range(2,10))
@pytest.mark.parametrize('num_tracks', [10])
def test_regression(num_tracks):
    params = {
        "width": 16,
        "num_tracks": num_tracks,
    }

    # Create magma circuit.
    magma_simple_cb = define_simple_cb(**params)
    res = compile_to_verilog(
        magma_simple_cb, magma_simple_cb.name, "test_simple_cb/build/")
    assert res

    # Create genesis circuit.
    genesis_simple_cb = define_simple_cb_wrapper(
        **params, input_files=["simple_cb/genesis/simple_cb.vp"])
    genesis_verilog = "genesis_verif/simple_cb.v"
    shutil.copy(genesis_verilog, "test_simple_cb/build/")

    # Introspect each circuit (get data inputs and width).
    genesis_inputs, genesis_width = parse_genesis_circuit(genesis_simple_cb)
    magma_input = magma_simple_cb.interface.ports["I"]

    # Check that the data input ports on the magma circuit match that of the
    # genesis circuit.
    assert magma_input.N == len(genesis_inputs)
    assert genesis_width == magma_input.T.N
    data_width = genesis_width

    testvectors = []

    # TODO: Do we need this extra instantiation, could the function do it for
    # us?
    simple_cb_functional_model = gen_simple_cb(**params)()

    tester = fault.Tester(genesis_simple_cb, clock=genesis_simple_cb.clk)

    config_addr = BitVector(0, 32)

    # Init inputs to 0.
    for i in range(num_tracks):
        tester.poke(getattr(genesis_simple_cb, f"in_{i}"), 0)

    for config_data in [BitVector(x, 32) for x in range(0, 1)]:
        simple_cb_functional_model.config[config_addr] = config_data
        tester.poke(genesis_simple_cb.clk, 0)
        tester.poke(genesis_simple_cb.reset, 0)
        tester.poke(genesis_simple_cb.config_addr, 0)
        tester.poke(genesis_simple_cb.config_data, 0)
        tester.poke(genesis_simple_cb.config_en, 1)
        # TODO: Technically we don't care about the output at this point,
        # ideally we could just not expect anything.
        tester.expect(genesis_simple_cb.out, 0)

        tester.step()

        # Posedge of clock, so simple_cb should now be configured.
        simple_cb_functional_model.config[config_addr] = config_data

        tester.expect(genesis_simple_cb.read_data,
                      simple_cb_functional_model.config[config_addr])
        tester.expect(genesis_simple_cb.read_data,
                      simple_cb_functional_model.config[config_addr])
        tester.expect(genesis_simple_cb.out, 0)  # 0 because inputs are 0

        tester.step()

        inputs = [random_bv(data_width) for _ in range(num_tracks)]
        _inputs = []
        for i in range(num_tracks):
            _inputs.append(inputs[i])
            tester.poke(getattr(genesis_simple_cb, f"in_{i}"), inputs[i])
        tester.expect(genesis_simple_cb.out,
                      simple_cb_functional_model(*_inputs))
        tester.eval()
    testvectors = tester.test_vectors

    # Right now this test won't work because the magma interface is not exactly
    # the same as the genesis interface. The magma circuit uses an array of
    # inputs, whereas genesis has flattened that into named inputs.
    # TODO(rsetaluri): Design a way to make these compatible. Some kind of
    # mapping between array inputs and names could do the job.
    """
    for simple_cb in [genesis_simple_cb, magma_simple_cb]:
        compile(f"test_simple_cb/build/test_{simple_cb.name}.cpp",
                simple_cb,
                testvectors)
        run_verilator_test(simple_cb.name, f"test_{simple_cb.name}",
                           simple_cb.name, ["-Wno-fatal"],
                           build_dir="test_simple_cb/build")
    """
