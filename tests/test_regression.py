import random
import shutil
import os
import glob
from bit_vector import BitVector

from connect_box.cb import define_cb
from connect_box.cb_functional_model import gen_cb
from connect_box.cb_wrapper import define_cb_wrapper

import magma as m
from magma.testing.verilator import compile, run_verilator_test
from util import make_relative

import pytest


def teardown_function():
    for item in glob.glob('genesis_*'):
        os.system(f"rm -r {item}")


def random_bv(width):
    return BitVector(random.randint(0, (1 << width) - 1), width)


@pytest.mark.parametrize('default_value,has_constant',
                         # Test 10 random default values with has_constant
                         [(random_bv(16), 1) for _ in range(2)] +
                         # include one test with no constant
                         [(random_bv(16), 0)])
# FIXME: this fails
# @pytest.mark.parametrize('num_tracks', range(2,10))
@pytest.mark.parametrize('num_tracks', [10])
def test_regression(default_value, num_tracks, has_constant):
    params = {
        "width": 16,
        "num_tracks": num_tracks,
        "feedthrough_outputs": "1111101111",
        "has_constant": has_constant,
        "default_value": default_value.as_int()
    }

    magma_cb = define_cb(**params)
    m.compile(f"build/{magma_cb.name}", magma_cb, output='coreir')
    json_file = make_relative(f"build/{magma_cb.name}.json")
    magma_verilog = make_relative(f"build/{magma_cb.name}.v")
    os.system(f'coreir -i {json_file} -o {magma_verilog}')

    genesis_cb = define_cb_wrapper(**params, filename=make_relative("cb.vp"))

    genesis_verilog = "genesis_verif/cb.v"
    shutil.copy(genesis_verilog, make_relative("build"))

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

    testvectors = []

    GND = BitVector(0, 1)
    VCC = BitVector(1, 1)

    # TODO: Do we need this extra instantiation, could the function do it for
    # us?
    cb_functional_model = gen_cb(**params)()

    # Generate the configuration sequence
    # Config logic
    ins = [GND for _ in range(len(inputs))]
    reset = GND
    config_addr = BitVector(0, 32)
    for config_data in [BitVector(x, 32) for x in range(0, len(inputs))]:
        config_en = VCC
        out = cb_functional_model(*ins)
        read_data = cb_functional_model.config[0]
        clk = GND
        vector = [clk, reset] + ins + [out, config_addr, config_data,
                                       config_en, read_data]
        testvectors.append(vector)
        clk = VCC
        # Step the clock
        cb_functional_model.configure(config_addr, config_data)
        read_data = cb_functional_model.config[0]
        out = cb_functional_model(*ins)
        vector = [clk, reset] + ins + [out, config_addr, config_data,
                                       config_en, read_data]
        testvectors.append(vector)

        ins = [random_bv(data_width) for _ in range(len(inputs))]
        reset = GND
        clk = GND
        config_en = GND
        out = cb_functional_model(*ins)
        print(out, ins, config_data)
        assert len(cb_functional_model.config) == 1
        vector = [clk, reset] + ins + [out, config_addr, config_data,
                                       config_en, read_data]
        testvectors.append(vector)

    for cb in [genesis_cb, magma_cb]:
        compile(f"build/test_{cb.name}.cpp", cb, testvectors)
        run_verilator_test(cb.name, f"test_{cb.name}", cb.name, ["-Wno-fatal"])
