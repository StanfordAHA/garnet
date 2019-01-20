from bit_vector import BitVector

from common.testers import BasicTester
from interconnect.cyclone import *
from interconnect.circuit import *
from common.core import Core
import magma
import tempfile
import fault
import fault.random
import pytest


class DummyCore(Core):
    def __init__(self):
        super().__init__()

        # PEP 8 rename
        t_data = magma.Bits(16)

        self.add_ports(
            data_in=magma.In(t_data),
            data_out=magma.Out(t_data),
        )

        self.wire(self.ports.data_in, self.ports.data_out)

    def inputs(self):
        return [self.ports.data_in]

    def outputs(self):
        return [self.ports.data_out]

    def name(self):
        return "DummyCore"


class DummyGenerator(generator.Generator):
    def __init__(self):
        super().__init__()

        t_data = magma.Bits(16)

        self.add_ports(
            data_in=magma.In(t_data),
            data_out=magma.Out(t_data),
        )

        self.wire(self.ports.data_in, self.ports.data_out)

    def name(self):
        return "DummyGenerator"


#@pytest.mark.parametrize('num_tracks', [2, 5])
#@pytest.mark.parametrize('bit_width', [1, 16])
def __test_cb(num_tracks: int, bit_width: int):
    addr_width = 8
    data_width = 32

    port_node = PortNode("data_in", 0, 0, bit_width)

    for i in range(num_tracks):
        sb = SwitchBoxNode(0, 0, i, bit_width, SwitchBoxSide.NORTH,
                           SwitchBoxIO.SB_IN)
        sb.add_edge(port_node)

    cb = CB(port_node, addr_width, data_width)

    assert cb.mux.height == num_tracks

    circuit = cb.circuit()

    # logic copied from test_simple_cb_magma
    tester = BasicTester(circuit,
                         circuit.clk,
                         circuit.reset)

    for config_data in [BitVector(x, data_width) for x in range(num_tracks)]:
        tester.reset()
        tester.configure(BitVector(0, addr_width), config_data)
        tester.configure(BitVector(0, addr_width), config_data + 1, False)
        tester.config_read(BitVector(0, addr_width))
        tester.eval()
        tester.expect(circuit.read_config_data, config_data)
        inputs = [fault.random.random_bv(bit_width) for _ in range(num_tracks)]
        for i, input_ in enumerate(inputs):
            tester.poke(circuit.I[i], input_)
        tester.eval()
        tester.expect(circuit.O, inputs[config_data.as_uint()])

    with tempfile.TemporaryDirectory() as tempdir:
        tester.compile_and_run(target="verilator",
                               magma_output="coreir-verilog",
                               directory=tempdir,
                               flags=["-Wno-fatal"])


@pytest.mark.parametrize('num_tracks', [2])
@pytest.mark.parametrize('bit_width', [1])
def test_disjoint_sb(num_tracks: int, bit_width: int):
    addr_width = 8
    data_width = 32

    switchbox = DisjointSwitchBox(0, 0, num_tracks, bit_width)
    sb = SB(switchbox, addr_width, data_width)
    circuit = sb.circuit()

    # test the sb routing as well
    tester = BasicTester(circuit,
                         circuit.clk,
                         circuit.reset)

    # generate the addr based on mux names, which is used to sort the addr
    config_names = list(sb.registers.keys())
    config_names.sort()

    for addr, config_name in enumerate(config_names):
        pass
