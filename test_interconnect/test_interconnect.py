from interconnect.interconnect import Interconnect, InterconnectType
from interconnect.interconnect import Tile, Switch, SwitchManager
from interconnect.interconnect import SwitchBoxSide, SwitchBoxIO
from interconnect.interconnect import SBConnectionType
from common.core import Core
import magma
from simple_sb.simple_sb_model import SimpleSBModel, SimpleSBTester, SideModel
import fault.random
import random
import tempfile


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


def test_switch_manager():
    sb_manager = SwitchManager()
    sb1 = sb_manager.create_disjoint_switch(1, 5)
    sb2 = sb_manager.create_disjoint_switch(1, 5)
    assert sb1.switchbox_.id == sb2.switchbox_.id
    # different ones
    sb3 = sb_manager.create_disjoint_switch(1, 1)
    assert sb3.switchbox_.id == sb1.switchbox_.id + 1


def test_switch():
    sb_manager = SwitchManager()
    switch = sb_manager.create_disjoint_switch(1, 5)
    track = 4
    node = switch[SwitchBoxSide.NORTH, track, SwitchBoxIO.IN]
    assert node.track == track


def test_tile():
    width = 16
    interconnect = Interconnect(width, InterconnectType.Mesh)
    sb_manager = SwitchManager()
    switch = sb_manager.create_disjoint_switch(1, 5)
    tile = Tile(0, 0, 1)
    interconnect.add_tile(tile, switch)
    # test add_tile basic
    assert interconnect.get_size() == (1, 1)
    tile = Tile(1, 2, 2)
    interconnect.add_tile(tile, switch)
    # test add_tile scale
    assert interconnect.get_size() == (2, 4)
    # test get tile
    tile_bottom = interconnect.get_tile(1, 3)
    assert tile_bottom == interconnect.get_tile(1, 2)
    assert tile_bottom == tile
    # test check empty
    assert interconnect.has_empty_tile()
    # test to string
    assert interconnect.name() == "Interconnect " + str(width)
    # test overlapping
    tile_overlap = Tile(1, 3, 1)
    try:
        interconnect.add_tile(tile_overlap, switch)
        assert False
    except RuntimeError:
        assert True
    # test other exceptions
    try:
        Interconnect(width, InterconnectType.Hierarchical)
        assert False
    except NotImplementedError:
        assert True
    assert interconnect.get_tile(10, 10) is None
    # test cyclone interaction
    t = interconnect.get_cyclone_tile(1, 2)
    assert t.x == 1 and t.y == 2


def test_tile_core():
    conn, interconnect, port_name = set_up_interconnect(is_conn_in=True)
    # check if it's there
    sb = interconnect.get_sb_node(0, 0, conn[0].side, conn[0].track, conn[0].io)
    nodes = list(sb)
    assert len(nodes) == 1
    str_eval = str(nodes[0])
    # use unique string representation to check equality, thus avoiding type
    # casting, which is awkward in Python
    port = interconnect.get_port_node(0, 0, port_name)
    assert str_eval == str(port)
    # also make sure that the conn_in is correct
    conn_in = list(port.get_conn_in())
    assert len(conn_in) == 1
    assert str(conn_in[0]) == str(sb)

    # test the same thing with out
    port_name = "data_out"
    conn = [SBConnectionType(SwitchBoxSide.NORTH, 0, SwitchBoxIO.OUT)]
    interconnect.set_core_connection_out(0, 0, port_name, conn)
    port = interconnect.get_port_node(0, 0, port_name)
    sb = interconnect.get_sb_node(0, 0, conn[0].side, conn[0].track, conn[0].io)
    nodes = list(port)
    assert len(nodes) == 1
    assert str(nodes[0]) == str(sb)


def set_up_interconnect(is_conn_in: bool, connect_all=False):
    width = 16
    num_track = 5
    port_name = "data_in" if is_conn_in else "data_out"
    interconnect = Interconnect(width, InterconnectType.Mesh)
    sb_manager = SwitchManager()
    switch = sb_manager.create_disjoint_switch(width, num_track)
    tile = Tile(0, 0, 1)
    interconnect.add_tile(tile, switch)
    interconnect.set_core(0, 0, DummyCore())
    # add connection to its switch boxes
    if not connect_all:
        conn = [SBConnectionType(SwitchBoxSide.NORTH, 1, SwitchBoxIO.OUT)]
    else:
        conn = []
        for side in SwitchBoxSide:
            for track in range(num_track):
                conn.append((SBConnectionType(side, track, SwitchBoxIO.OUT)))
    if is_conn_in:
        interconnect.set_core_connection_in(0, 0, port_name, conn)
    else:
        interconnect.set_core_connection_out(0, 0, port_name, conn)
    return conn, interconnect, port_name


def __test_switch_sb():
    # FIXME: this test is broken. need to figure out where it fails
    conn, interconnect, port_name = set_up_interconnect(is_conn_in=False,
                                                        connect_all=True)
    sbs, _ = interconnect.realize()
    assert len(sbs) == 1
    simple_sb = sbs[0]

    # parameters
    num_track = 5
    layers = [16]
    num_core_outputs = 1
    sides = ("north", "west", "south", "east")

    # copy the old sb regression test
    # rename variables to meet PEP 8's standards
    simple_sb_circuit = simple_sb.circuit()
    tester = fault.Tester(simple_sb_circuit, simple_sb_circuit.clk)
    model = SimpleSBModel(num_track, layers, num_core_outputs)
    simple_sb_tester = SimpleSBTester(
        num_track, layers, num_core_outputs, model, tester)

    config = {side: SideModel(num_track, layers) for side in sides}
    in_ = {side: SideModel(num_track, layers) for side in sides}

    for side in sides:
        for layer in layers:
            for track in range(num_track):
                config[side].values[layer][track] = random.randint(0, 3)
                in_[side].values[layer][track] = fault.random.random_bv(layer)

    core_outputs = {
        "data_out": fault.random.random_bv(16)
    }

    simple_sb_tester.reset()
    simple_sb_tester.configure(config)
    simple_sb_tester(in_, core_outputs)

    with tempfile.TemporaryDirectory() as tempdir:
        simple_sb_tester.tester.compile_and_run(target="verilator",
                                                magma_output="coreir-verilog",
                                                directory=tempdir,
                                                flags=["-Wno-fatal"])
