from bit_vector import BitVector
from common.dummy_core_magma import DummyCore
from common.testers import BasicTester
from interconnect.cyclone import *
from interconnect.circuit import *
import tempfile
import fault
import fault.random
import pytest


@pytest.mark.parametrize('num_tracks', [2, 5])
@pytest.mark.parametrize('bit_width', [1, 16])
def _test_cb(num_tracks: int, bit_width: int):
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
def _test_sb(num_tracks: int, bit_width: int, sb_ctor):
    """It only tests whether the circuit created matched with the graph
       representation.
    """
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

    with tempfile.TemporaryDirectory() as tempdir:
        tester.compile_and_run(target="verilator",
                               magma_output="coreir-verilog",
                               directory=tempdir,
                               flags=["-Wno-fatal"])


# 5 is too slow
@pytest.mark.parametrize('num_tracks', [2, 4])
def test_tile(num_tracks: int):
    addr_width = 8
    data_width = 32
    bit_widths = [1, 16]

    tile_id_width = 16
    x = 0
    y = 0

    dummy_core = DummyCore()
    core = CoreInterface(dummy_core)

    tiles: Dict[int, Tile] = {}

    for bit_width in bit_widths:
        # we use disjoint switch here
        switchbox = DisjointSwitchBox(x, y, num_tracks, bit_width)
        tile = Tile(x, y, bit_width, switchbox)
        tiles[bit_width] = tile

    # set the core and core connection
    # here all the input ports are connect to SB_IN and all output ports are
    # connected to SB_OUT
    input_connections = []
    for track in range(num_tracks):
        for side in SwitchBoxSide:
            input_connections.append(SBConnectionType(side, track,
                                                      SwitchBoxIO.SB_IN))
    output_connections = []
    for track in range(num_tracks):
        for side in SwitchBoxSide:
            output_connections.append(SBConnectionType(side, track,
                                                       SwitchBoxIO.SB_OUT))
    input_names: List[Tuple[str, int]] = []
    output_names: List[Tuple[str, int]] = []
    for bit_width, tile in tiles.items():
        tile.set_core(core)
        input_port_name = f"data_in_{bit_width}b"
        output_port_name = f"data_out_{bit_width}b"

        tile.set_core_connection(input_port_name, input_connections)
        tile.set_core_connection(output_port_name, output_connections)

        input_names.append((input_port_name, bit_width))
        output_names.append((output_port_name, bit_width))

    tile_circuit = TileCircuit(tiles, addr_width, data_width,
                               tile_id_width=tile_id_width)

    circuit = tile_circuit.circuit()

    # set up the configuration and test data
    # there are several things we are interested in the tile level and
    # need to test
    # 1. given an input to SB_IN, and configure it to CB, will the core
    # receive the data or not
    # 2. given an output signal from core, and configure it to SB, will the
    # SB_OUT receive the data or not
    # However, because we can only poke input ports, we cannot test #2 in the
    # current environment. As a result, we will combined these 2 together, that
    # is:
    # given an SB_IN signal, we configure the CB to the data_in, then configure
    # the SB_OUT to receive the signal
    raw_config_data = []
    config_data = []
    test_data = []
    tile_id = fault.random.random_bv(tile_id_width)

    for bit_width in bit_widths:
        # find corresponding sb
        sb_circuit: SB = None
        for _, sb in tile_circuit.sbs.items():
            if sb.switchbox.width == bit_width:
                sb_circuit = sb
                break
        assert sb_circuit is not None
        # find feature addr
        sb_feature_addr = tile_circuit.features().index(sb_circuit)

        # input
        input_port_name = f"data_in_{bit_width}b"
        in_port_node = tile_circuit.tiles[bit_width].ports[input_port_name]
        # find that connection box
        cb_circuit: CB = None
        for _, cb in tile_circuit.cbs.items():
            if cb.node.name == input_port_name:
                cb_circuit = cb
                break
        assert cb_circuit

        output_port_name = f"data_out_{bit_width}b"
        out_port_node = tile_circuit.tiles[bit_width].ports[output_port_name]

        all_sbs = sb_circuit.switchbox.get_all_sbs()
        for in_sb_node in all_sbs:
            if in_sb_node.io != SwitchBoxIO.SB_IN:
                continue

            for out_sb_node in all_sbs:
                if out_sb_node.io != SwitchBoxIO.SB_OUT:
                    continue
                # find the output node's index to that switch box node
                data0 = tile_circuit.get_route_bitstream_config(in_sb_node,
                                                                in_port_node)
                data1 = tile_circuit.get_route_bitstream_config(out_port_node,
                                                                out_sb_node)
                raw_config_data.append(data0)

                raw_config_data.append(data1)

                in_sb_name = create_name(str(in_sb_node))
                out_sb_name = create_name(str(out_sb_node))
                test_data.append((circuit.interface.ports[in_sb_name],
                                  circuit.interface.ports[out_sb_name],
                                  fault.random.random_bv(bit_width)))

    # process the raw config data and change it into the actual config addr
    for addr, config_value in raw_config_data:
        addr = BitVector(addr, data_width) | tile_id
        config_data.append((addr, config_value))

    assert len(config_data) / 2 == len(test_data)

    # actual tests
    tester = BasicTester(circuit, circuit.clk, circuit.reset)
    tester.poke(circuit.tile_id, tile_id)

    for i in range(0, len(config_data), 2):
        tester.reset()
        addr, config_value = config_data[i]
        tester.configure(addr, config_value)
        tester.configure(addr, config_value + 1, False)
        tester.config_read(addr)
        tester.eval()
        tester.expect(circuit.read_config_data, config_value)

        addr, config_value = config_data[i + 1]
        tester.configure(addr, config_value)
        tester.configure(addr, config_value + 1, False)
        tester.config_read(addr)
        tester.eval()
        tester.expect(circuit.read_config_data, config_value)

        input_port, output_port, value = test_data[i // 2]

        tester.poke(input_port, value)
        tester.eval()
        tester.expect(output_port, value)

    with tempfile.TemporaryDirectory() as tempdir:
        tester.compile_and_run(target="verilator",
                               magma_output="coreir-verilog",
                               directory=tempdir,
                               flags=["-Wno-fatal"])
