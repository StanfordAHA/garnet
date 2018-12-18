import tempfile
import random
import fault
import fault.random
from common.dummy_core_magma import DummyCore
from common.testers import BasicTester
from simple_sb.simple_sb_magma import SB
from simple_sb.simple_sb_model import SideModel


def test_regression():
    # Create magma circuit.
    dummy_core = DummyCore()
    simple_sb = SB(dummy_core.outputs())

    for output in dummy_core.outputs():
        port_name = output._name
        port = simple_sb.ports.get(port_name, None)
        assert port is not None
        assert port.type() == output.type().flip()

    NUM_TRACKS = 5
    LAYERS = (1, 16)
    SIDES = ("north", "west", "south", "east")

    simple_sb_circuit = simple_sb.circuit()

    # create random test data
    # first batch all buffers configured off
    # second batch all buffers confgured on
    # third batch buffer configuration randomized
    configs = []
    inputs = []
    core_outputs = []
    NUM_BATCHES = 3
    BATCH_LEN = 100

    # initialize datastructures for holding test data
    for batch in range(NUM_BATCHES):
        config = {side: SideModel(NUM_TRACKS, LAYERS) for side in SIDES}
        configs.append(config)
        in_ = {side: SideModel(NUM_TRACKS, LAYERS) for side in SIDES}
        inputs.append(in_)
        core_outputs_dict = {}
        core_outputs.append(core_outputs_dict)

    # create random test data
    for batch in range(NUM_BATCHES):
        for side in SIDES:
            for layer in LAYERS:
                for track in range(NUM_TRACKS):
                    # decide on which register buffers to enable
                    if batch == 0:
                        buffer_config = 0
                    elif batch == 1:
                        buffer_config = 1
                    else:
                        buffer_config = random.randint(0, 1)

                    configs[batch][side].values[layer][track] = \
                        (random.randint(0, 3), buffer_config)
                    batch_inputs = [fault.random.random_bv(layer)
                                    for _ in range(BATCH_LEN)]
                    inputs[batch][side].values[layer][track] = batch_inputs
                    core_outputs_batch_data = \
                        [fault.random.random_bv(16) for _ in range(BATCH_LEN)]
                    core_outputs_batch_bits = \
                        [fault.random.random_bv(1) for _ in range(BATCH_LEN)]
                    core_outputs[batch]["data_out_16b"] = \
                        core_outputs_batch_data
                    core_outputs[batch]["data_out_1b"] = \
                        core_outputs_batch_bits

    # This function taken from the model, with minor updates
    # finds mux output before register buffer based on:
    # inputs core_outputs configs
    def get_output(side, layer, track, batch, step):
        buffer_config = configs[batch][side].values[layer][track][1]
        relevant_step = step-1 if buffer_config else step
        mux_inputs = []
        for other_side in SIDES:
            if other_side == side:
                continue
            mux_inputs.append(
                inputs[batch][other_side].values[layer][track][relevant_step])
        # TODO(rsetaluri): Abstract this part out. Right now it is a
        # hard coded hack.
        if layer == 16:
            mux_inputs.append(
                core_outputs[batch]["data_out_16b"][relevant_step])
        else:
            mux_inputs.append(
                core_outputs[batch]["data_out_1b"][relevant_step])
        select = configs[batch][side].values[layer][track][0]
        return mux_inputs[select]

    basic_tester = BasicTester(simple_sb_circuit, simple_sb_circuit.clk,
                               simple_sb_circuit.reset)

    # run each batch of tests
    for batch in range(NUM_BATCHES):
        # configure, once per batch
        basic_tester.reset()
        addr = 0
        for side in SIDES:
            for layer in LAYERS:
                for track in range(NUM_TRACKS):
                    # configure muxes
                    this_config = configs[batch][side].values[layer][track]
                    basic_tester.configure(addr, this_config[0])
                    basic_tester.config_read(addr)
                    basic_tester.expect(simple_sb_circuit.read_config_data,
                                        this_config[0])
                    addr = addr + 1

                    # confiture registers
                    basic_tester.configure(addr, this_config[1])
                    basic_tester.config_read(addr)
                    basic_tester.expect(simple_sb_circuit.read_config_data,
                                        this_config[1])
                    addr = addr + 1

        for step in range(BATCH_LEN):
            # poke inputs, many times per batch
            basic_tester.step(3)
            for name, values in core_outputs[batch].items():
                value = values[step]
                port = simple_sb_circuit.interface.ports[name]
                basic_tester.poke(port, value)
            for side in SIDES:
                for layer in LAYERS:
                    for track in range(NUM_TRACKS):
                        side_ports = simple_sb_circuit.interface.ports[side].I
                        in_port = getattr(side_ports, f"layer{layer}")[track]
                        value = inputs[batch][side].values[layer][track][step]
                        basic_tester.poke(in_port, value)
            basic_tester.eval()

            # expect outputs, once for each time we poke inputs
            if step == 0:
                # Can't expect on step zero because we don't know what was
                # sitting in register buffers
                continue
            for side in SIDES:
                for layer in LAYERS:
                    for track in range(NUM_TRACKS):
                        expected = get_output(side, layer, track, batch, step)
                        side_ports = simple_sb_circuit.interface.ports[side].O
                        out_port = getattr(side_ports, f"layer{layer}")[track]
                        basic_tester.expect(out_port, expected)

    # run test
    with tempfile.TemporaryDirectory() as tempdir:
        basic_tester.compile_and_run(target="verilator",
                                     magma_output="coreir-verilog",
                                     directory=tempdir,
                                     flags=["-Wno-fatal"])
