from interconnect.circuit import CB, SwitchBoxMux, EmptyCircuit
from interconnect.cyclone import PortNode, SwitchBoxNode, SwitchBoxSide
from interconnect.cyclone import SwitchBoxIO
from interconnect.sb import DisjointSB, WiltonSB, ImranSB
from interconnect.tile_circuit import TileCircuit, SBConnectionType
from common.core import Core
import magma


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


def test_connection():
    """test low-level add/remove connections"""
    # USAGE
    x = 0
    y = 0
    track = 0
    bit_width = 16
    port_node = PortNode("data_in", x, y, bit_width)
    sb_node = SwitchBoxNode(x, y, track, bit_width, SwitchBoxSide.EAST,
                            SwitchBoxIO.SB_IN)
    core = DummyCore()
    cb = CB(port_node, core.ports.data_in)
    sb = SwitchBoxMux(sb_node)
    sb.connect(cb)

    # TESTS
    # test connectivity
    assert sb.is_connected(cb)
    assert not cb.is_connected(sb)

    # test disconnect
    # try reverse order first
    cb.disconnect(sb)
    assert sb.is_connected(cb)
    # actually disconnect
    sb.disconnect(cb)
    assert not sb.is_connected(cb)


def test_circuit_create():
    """tests low level circuit creation, that is, if the users wants to get
    their hands dirty"""
    # USAGE
    x = 0
    y = 0
    track = 0
    bit_width = 16
    port_node = PortNode("data_in", x, y, bit_width)
    sb_node1 = SwitchBoxNode(x, y, track, bit_width, SwitchBoxSide.EAST,
                             SwitchBoxIO.SB_IN)
    sb_node2 = SwitchBoxNode(x, y + 1, track, bit_width, SwitchBoxSide.EAST,
                             SwitchBoxIO.SB_IN)
    core = DummyCore()
    cb = CB(port_node, core.ports.data_in)
    sb1 = SwitchBoxMux(sb_node1)
    sb2 = SwitchBoxMux(sb_node2)

    # create a mux-like connection the cb has two incoming track connections
    sb1.connect(cb)
    sb2.connect(cb)

    # realize the circuit
    sb1.realize()
    sb2.realize()
    cb.realize()

    # TESTS
    # test the circuit created
    assert cb.mux is not None
    assert cb.mux.height == 2
    # test if the underlying circuit is actually connected
    assert len(sb1.wires) == 1
    port1, port2 = sb1.wires[0]
    # because wire() will reorder the ports, we need to compare them
    # with caution
    assert (port1.owner() == sb1.mux and port2.owner() == cb.mux) or \
           (port1.owner() == cb.mux and port2.owner() == sb1.mux)


def test_sb():
    """test high-level SB creation"""
    # USAGE
    # test disjoint switchbox
    x = 0
    y = 0
    bit_width = 16
    num_track = 2
    disjoint = DisjointSB(x, y, bit_width, num_track)
    wilton = WiltonSB(x, y, bit_width, num_track)
    imran = ImranSB(x, y, bit_width, num_track)

    disjoint.realize()
    wilton.realize()
    imran.realize()

    # TESTS
    # test number of sb muxs created
    assert len(disjoint.muxs) == 2 * 4 * 2

    # test connectivity
    # because it's disjoint, each side has incoming connections coming from
    # the other sides on the same track
    for track in range(num_track):
        for side in SwitchBoxSide:
            sb_mux = disjoint[side][SwitchBoxIO.SB_OUT.value][track]

            for side_from in SwitchBoxSide:
                if side_from == side:
                    continue
                sb_mux_from =\
                    disjoint[side_from][SwitchBoxIO.SB_IN.value][track]
                # they have to be connected
                assert sb_mux_from.is_connected(sb_mux)
                # test ownership
                assert sb_mux in disjoint
                assert sb_mux not in wilton
                assert sb_mux not in imran

    # only test pass through in wilton and imran
    # TODO: add more tests on the side turning tracks
    for track in range(num_track):
        for side in SwitchBoxSide:
            # wilton
            sb_mux = wilton[side][SwitchBoxIO.SB_OUT.value][track]
            op_side = SwitchBoxSide.get_opposite_side(side)
            sb_mux_from = \
                wilton[op_side.value][SwitchBoxIO.SB_IN.value][track]
            assert sb_mux_from.is_connected(sb_mux)

            # imran
            sb_mux = imran[side][SwitchBoxIO.SB_OUT.value][track]
            op_side = SwitchBoxSide.get_opposite_side(side)
            sb_mux_from = \
                imran[op_side.value][SwitchBoxIO.SB_IN.value][track]
            assert sb_mux_from.is_connected(sb_mux)


def test_tile_circuit():
    # USAGE
    x = 0
    y = 0
    bit_width = 16
    num_track = 2
    height = 1

    # create a disjoint SB and the tile that uses it
    disjoint = DisjointSB(x, y, bit_width, num_track)
    tile = TileCircuit.create(disjoint, height)
    pe_core = DummyCore()
    # snap the core to the interconnect tile
    tile.set_core(pe_core)

    # set connections. to all sb output
    out_conns = []
    in_conns = []
    for side in SwitchBoxSide:
        for track in range(num_track):
            out_conns.append(SBConnectionType(side, track, SwitchBoxIO.SB_OUT))
            in_conns.append((SBConnectionType(side, track, SwitchBoxIO.SB_IN)))
    # let data_out port connect to every sb out on each side and every track
    tile.set_core_connection("data_out", out_conns)
    # data_in from every input sb mux
    tile.set_core_connection("data_in", in_conns)
    # realize the circuit
    tile.realize()

    # TESTS
    out_circuit = tile.get_port_circuit("data_out")
    in_circuit = tile.get_port_circuit("data_in")
    # we don't create CB for output ports
    assert isinstance(out_circuit, EmptyCircuit)
    assert isinstance(in_circuit, CB)
    assert in_circuit.mux is not None
    assert out_circuit in tile
    assert in_circuit in tile

    # test input connectivity
    assert len(in_circuit.wires) == 1
    connected = False
    for conn in in_circuit.wires[0]:
        if conn.owner() == pe_core:
            connected = True
            break
    assert connected

    # for a disjoint switch with 2 tracks and one input from every in track,
    # the cb mux will have 4 * 2 = 8 as height
    assert in_circuit.mux.height == 8
    # test the connection individually
    indices = set()
    for side in SwitchBoxSide:
        for track in range(num_track):
            sb_mux = tile.get_sb_circuit(side, track, SwitchBoxIO.SB_IN)
            for wire in sb_mux.wires:
                for conn in wire:
                    if conn.owner() == in_circuit.mux:
                        index = conn._ops[0].index
                        indices.add(index)
    assert len(indices) == 8

    # for a disjoint switch with one output to every out track,
    # each output mux will have 3 + 1 = 4 as height
    for side in SwitchBoxSide:
        for track in range(num_track):
            sb_mux = tile.get_sb_circuit(side, track, SwitchBoxIO.SB_OUT)
            assert sb_mux.mux is not None
            assert sb_mux.mux.height == 4
            # it's in the tile
            assert sb_mux in tile

            # test the connections
            sides = set()
            indices = set()
            for from_side in SwitchBoxSide:
                from_sb_mux = tile.get_sb_circuit(from_side, track,
                                                  SwitchBoxIO.SB_IN)
                for conns in from_sb_mux.wires:
                    for conn in conns:
                        owner = conn.owner()
                        if owner == sb_mux.mux:
                            sides.add(from_side)
                            index = conn._ops[0].index
                            indices.add(index)

            assert len(sides) == 3
            assert len(indices) == 3
            # found the mux connection with the data port
            found = False
            for wire in out_circuit.wires:
                for conn in wire:
                    if conn.owner() == sb_mux.mux:
                        found = True
                        break
            assert found
