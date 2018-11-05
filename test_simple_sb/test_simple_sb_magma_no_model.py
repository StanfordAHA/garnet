import pytest
import tempfile
import random
from bit_vector import BitVector
import magma
import fault
import fault.random
from common.core import Core
from common.testers import BasicTester
from simple_sb.simple_sb_magma import SB
from simple_sb.simple_sb_model import SimpleSBModel, SimpleSBTester, SideModel


class DummyCore(Core):
    def __init__(self):
        super().__init__()

        TData = magma.Bits(16)
        TBit = magma.Bits(1)

        self.add_ports(
            data_in=magma.In(TData),
            bit_in=magma.In(TBit),
            data_out=magma.Out(TData),
            bit_out=magma.Out(TBit),
        )

        self.wire(self.ports.data_in, self.ports.data_out)
        self.wire(self.ports.bit_in, self.ports.bit_out)

    def inputs(self):
        return (self.ports.data_in, self.ports.bit_in)

    def outputs(self):
        return (self.ports.data_out, self.ports.bit_out)

    def name(self):
        return "DummyCore"


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
    num_core_outputs = len(dummy_core.outputs())

    simple_sb_circuit = simple_sb.circuit()
    #tester = fault.Tester(simple_sb_circuit, simple_sb_circuit.clk)
    #model = SimpleSBModel(NUM_TRACKS, LAYERS, num_core_outputs)
    #simple_sb_tester = SimpleSBTester(
    #    NUM_TRACKS, LAYERS, num_core_outputs, model, tester)

    config = {side: SideModel(NUM_TRACKS, LAYERS) for side in SIDES}
    in1_ = {side: SideModel(NUM_TRACKS, LAYERS) for side in SIDES}
    in2_ = {side: SideModel(NUM_TRACKS, LAYERS) for side in SIDES}

    for side in SIDES:
        for layer in LAYERS:
            for track in range(NUM_TRACKS):
                config[side].values[layer][track] = (random.randint(0, 3), random.randint(0,1))
                in1_[side].values[layer][track] = fault.random.random_bv(layer)
                in2_[side].values[layer][track] = fault.random.random_bv(layer)

    core_outputs1 = {
        "data_out": fault.random.random_bv(16),
        "bit_out": fault.random.random_bv(1),
    }
    core_outputs2 = {
        "data_out": fault.random.random_bv(16),
        "bit_out": fault.random.random_bv(1),
    }


    # This function taken from the model, with update to look only at sel part of config
    # finds mux output before register buffer based on in_ core_outputs config
    def get_output(side, layer, track, in_, core_outputs):
        inputs = []
        for other_side in SIDES:
            if other_side == side:
                continue
            inputs.append(in_[other_side].values[layer][track])
        # TODO(rsetaluri): Abstract this part out. Right now it is a
        # hard coded hack.
        inputs.append(core_outputs["data_out"] if layer == 16
                      else core_outputs["bit_out"])
        select = config[side].values[layer][track][0]
        return  inputs[select]

    basic_tester = BasicTester(simple_sb_circuit, simple_sb_circuit.clk, simple_sb_circuit.reset)

    # configure
    basic_tester.reset()
    addr = 0
    for side in SIDES:
        for layer in LAYERS:
            for track in range(NUM_TRACKS):
                this_config = config[side].values[layer][track]
                basic_tester.configure(addr, this_config[0])
                basic_tester.config_read(addr)
                basic_tester.expect(simple_sb_circuit.read_config_data, this_config[0])
                addr = addr + 1
                basic_tester.configure(addr, this_config[1])
                basic_tester.config_read(addr)
                basic_tester.expect(simple_sb_circuit.read_config_data, this_config[1])
                addr = addr + 1

    # poke inputs
    for core_outputs, in_ in zip([core_outputs1, core_outputs2], [in1_, in2_]):
        basic_tester.step(2)
        for name, value in core_outputs.items():
            port = simple_sb_circuit.interface.ports[name]
            basic_tester.poke(port, value)
        for side in SIDES:
            for layer in LAYERS:
                for track in range(NUM_TRACKS):
                    in_port = getattr(simple_sb_circuit.interface.ports[side].I, f"layer{layer}")[track]
                    basic_tester.poke(in_port, in_[side].values[layer][track])
    basic_tester.eval()

    # expect outputs
    for side in SIDES:
        for layer in LAYERS:
            for track in range(NUM_TRACKS):
                if config[side].values[layer][track][1] == 0:
                    # not buffered
                    expected = get_output(side, layer, track, in2_, core_outputs2)
                else:
                    # buffered
                    expected = get_output(side, layer, track, in1_, core_outputs1)

                out_port = getattr(simple_sb_circuit.interface.ports[side].O, f"layer{layer}")[track]
                basic_tester.expect(out_port, expected)


    with tempfile.TemporaryDirectory() as tempdir:
        basic_tester.compile_and_run(target="verilator",
                                                magma_output="coreir-verilog",
                                                directory=tempdir,
                                                flags=["-Wno-fatal"])
