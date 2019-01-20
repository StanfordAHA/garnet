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


@pytest.mark.parametrize('num_tracks', [2, 5])
@pytest.mark.parametrize('bit_width', [1, 16])
@pytest.mark.parametrize("sb_ctor", [DisjointSwitchBox,
                                     WiltonSwitchBox, ImranSwitchBox])
def test_disjoint_sb(num_tracks: int, bit_width: int, sb_ctor):
    addr_width = 8
    data_width = 32

    switchbox = sb_ctor(0, 0, num_tracks, bit_width)
    sb_circuit = SB(switchbox, addr_width, data_width)
    circuit = sb_circuit.circuit()

    # test the sb routing as well
    tester = BasicTester(circuit,
                         circuit.clk,
                         circuit.reset)

    # generate the addr based on mux names, which is used to sort the addr
    config_names = list(sb_circuit.registers.keys())
    config_names.sort()

    # some of the sb nodes may turn into a pass-through wire. we still
    # need to test them.
    # we generate a pair of config data and expected values. if it's a
    # pass-through wire, we don't configure them, yet we still evaluate the
    # outcome to see if it's connected
    config_data = []
    test_data = []
    all_sbs = switchbox.get_all_sbs()
    for sb in all_sbs:
        mux_sel_name = get_mux_sel_name(sb)
        if mux_sel_name not in config_names:
            assert sb.io == SwitchBoxIO.SB_IN
            connected_sbs = sb.get_conn_in()
            # for a switch box where each SB_IN connects to 3 different
            # SN_OUT, the SB_IN won't have any incoming edges
            assert len(connected_sbs) == 0
            input_sb_name = create_name(str(sb))
            assert sb_circuit.sb_names[input_sb_name] == SwitchBoxIO.SB_IN
            # as a result, we configure the fan-out sbs to see if they
            # can receive the signal. notice that this is overlapped with the
            # if statement above
            for connected_sb in sb:
                mux_sel_name = get_mux_sel_name(connected_sb)
                assert mux_sel_name in config_names
                addr = config_names.index(mux_sel_name)
                index = connected_sb.get_conn_in().index(sb)
                config_data.append((addr, index))
                # get port
                output_sb_name = create_name(str(connected_sb))
                test_data.append((circuit.interface.ports[input_sb_name],
                                  circuit.interface.ports[output_sb_name],
                                  fault.random.random_bv(bit_width)))

    # poke and test
    assert len(config_data) == len(test_data)
    for i in range(len(config_data)):
        addr, index = config_data[i]
        input_port, output_port, value = test_data[i]
        index = BitVector(index, data_width)
        tester.reset()
        tester.configure(BitVector(addr, addr_width), index)
        tester.configure(BitVector(addr, addr_width), index + 1, False)
        tester.config_read(BitVector(addr, addr_width))
        tester.eval()
        tester.expect(circuit.read_config_data, index)
        tester.poke(input_port, value)
        tester.eval()
        tester.expect(output_port, value)

