import random
import shutil
import os
import glob
import functools
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


def convert_value(fn):
    @functools.wraps(fn)
    def wrapped(self, port, value):
        if isinstance(port, m.ArrayType) and isinstance(value, int):
            value = BitVector(value, len(port))
        elif isinstance(port, m._BitType) and isinstance(value, int):
            value = BitVector(value, 1)
        return fn(self, port, value)
    return wrapped


class Tester:
    def __init__(self, circuit, clock=None):
        self.circuit = circuit
        self.test_vectors = []
        self.port_index_mapping = {}
        self.ports = self.circuit.interface.ports
        self.clock_index = None
        for i, (key, value) in enumerate(self.ports.items()):
            self.port_index_mapping[value] = i
            if value is clock:
                self.clock_index = i
        # Initialize first test vector to all Nones
        self.test_vectors.append(
            [BitVector(None, 1 if isinstance(port, m.BitType) else len(port))
             for port in self.ports.values()])

    def get_index(self, port):
        return self.port_index_mapping[port]

    @convert_value
    def poke(self, port, value):
        if port.isinput():
            raise ValueError(f"Can only poke an input: {port} {type(port)}")
        self.test_vectors[-1][self.get_index(port)] = value

    @convert_value
    def expect(self, port, value):
        if port.isoutput():
            raise ValueError(f"Can only expect an output: {port} {type(port)}")
        self.test_vectors[-1][self.get_index(port)] = value

    def eval(self):
        self.test_vectors.append(self.test_vectors[-1][:])

    def step(self):
        self.eval()
        self.test_vectors[-1][self.clock_index] ^= BitVector(1, 1)
        self.eval()


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

    # TODO: Do we need this extra instantiation, could the function do it for
    # us?
    cb_functional_model = gen_cb(**params)()

    tester = Tester(genesis_cb, clock=genesis_cb.clk)

    config_addr = BitVector(0, 32)

    # init inputs to 0
    for i in range(0, num_tracks):
        if feedthrough_outputs[i] == "1":
            tester.poke(getattr(genesis_cb, f"in_{i}"), 0)

    for config_data in [BitVector(x, 32) for x in range(0, 1)]:
        tester.poke(genesis_cb.clk, 0)
        tester.poke(genesis_cb.reset, 0)
        tester.poke(genesis_cb.config_addr, 0)
        tester.poke(genesis_cb.config_data, 0)
        tester.poke(genesis_cb.config_en, 1)
        # TODO: Technically we don't care about the output at this point,
        # ideally we could just not expect anything
        tester.expect(genesis_cb.out, 0)
        tester.expect(genesis_cb.read_data, cb_functional_model.config[0])

        tester.step()

        # posedge of clock, so cb should now be configured
        cb_functional_model.configure(config_addr, config_data)

        tester.expect(genesis_cb.read_data, cb_functional_model.config[0])
        tester.expect(genesis_cb.read_data, cb_functional_model.config[0])
        tester.expect(genesis_cb.out, 0)  # 0 because inputs are 0

        tester.step()

        inputs = [random_bv(data_width) for _ in range(num_tracks)]
        _inputs = []
        for i in range(0, num_tracks):
            if feedthrough_outputs[i] == "1":
                _inputs.append(inputs[i])
                tester.poke(getattr(genesis_cb, f"in_{i}"), inputs[i])
        tester.expect(genesis_cb.out, cb_functional_model(*_inputs))
        tester.eval()
    testvectors = tester.test_vectors
    print(testvectors)

    for cb in [genesis_cb, magma_cb]:
        compile(f"build/test_{cb.name}.cpp", cb, testvectors)
        run_verilator_test(cb.name, f"test_{cb.name}", cb.name, ["-Wno-fatal"])
