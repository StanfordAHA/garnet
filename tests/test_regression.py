import random
import os
from bit_vector import BitVector

from connect_box.build_cb_top import define_connect_box
from connect_box.genesis_wrapper import run_genesis

import magma as m
from util import make_relative


def test_regression():
    params = {
        "width": 16,
        "num_tracks": 10,
        "feedthrough_outputs": "1111101111",
        # "has_constant": 1,  Mismatch in reset logic makes this case fail
        "has_constant": 0,
        "default_value": 7
    }

    run_genesis("cb", make_relative("cb.vp"), params)

    magma_cb = define_connect_box(**params)
    m.compile(magma_cb.name, magma_cb, output='coreir')
    json_file = make_relative(f"{magma_cb.name}.json")
    os.system(f'coreir -i {json_file} -o {magma_cb.name}.v')

    magma_verilog = f"{magma_cb.name}.v"
    genesis_verilog = "genesis_verif/cb.v"

    genesis_cb = m.DefineFromVerilogFile(genesis_verilog)[-1]

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

    # Generate the configuration sequence
    # Config logic
    ins = [GND for _ in range(len(inputs))]
    reset = GND
    config_addr = GND
    config_data = GND
    config_en = GND
    out = GND
    read_data = GND
    vector = [reset] + ins + [out, config_addr, config_data, config_en,
                              read_data]
    # Twiddle the clock 3 times
    for i in range(3):
        testvectors.append([BitVector(i % 2, 1)] + vector)

    ins = [BitVector(random.randint(0, (1 << data_width) - 1), data_width)
           for _ in range(len(inputs))]
    reset = GND
    clk = GND
    config_addr = BitVector(random.randint(0, 1 << 31), 32)
    config_data = BitVector(random.randint(0, 1 << 31), 32)
    config_en = GND
    out = ins[0]
    vector = [clk, reset] + ins + [out, config_addr, config_data, config_en,
                                   read_data]
    testvectors.append(vector)

    from magma.testing.verilator import compile, run_verilator_test
    import shutil
    for cb, file in [(genesis_cb, genesis_verilog), (magma_cb, magma_verilog)]:
        compile(f"build/test_{cb.name}.cpp", cb, testvectors)
        shutil.copy(file, make_relative("build"))
        run_verilator_test(cb.name, f"test_{cb.name}", cb.name, ["-Wno-fatal"])
