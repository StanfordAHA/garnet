from interconnect.interconnect import Interconnect, InterconnectType
from interconnect.cyclone import Tile as GTile
from interconnect.cyclone import SwitchBoxSide, SwitchBoxIO
from interconnect.util import create_uniform_interconnect
from interconnect.interconnect import TileCircuit
from interconnect.sb import SwitchBoxType
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


def test_tiling():
    """test low-level tiling. we expect the tiling be handled internally.
    as a result, users do not need to create a graph tile by hand
    """
    width = 16
    interconnect = Interconnect(width, InterconnectType.Mesh)
    tile1 = TileCircuit(GTile.create_tile(0, 0, 1, 16, []))
    interconnect.add_tile(tile1)
    # now we have the following layout
    # |-0-|
    assert interconnect.get_size() == (1, 1)

    tile2 = TileCircuit(GTile.create_tile(1, 2, 1, 16, [], height=2))
    interconnect.add_tile(tile2)
    # now we have the following layout
    # |-0-|---|
    # |---|---|
    # |---|-1-|
    # |---|-1-|
    assert interconnect.get_size() == (2, 4)
    # test get tile
    tile_bottom = interconnect.get_tile(1, 3)
    assert tile_bottom == interconnect.get_tile(1, 2)
    assert tile_bottom == tile2
    # test check empty
    assert interconnect.has_empty_tile()

    # we just adding two more tiles to make it full
    tile2 = TileCircuit(GTile.create_tile(0, 1, 1, 16, [], height=3))
    interconnect.add_tile(tile2)
    # now we have the following layout
    # |-0-|---|
    # |-2-|---|
    # |-2-|-1-|
    # |-2-|-1-|
    tile3 = TileCircuit(GTile.create_tile(1, 0, 1, 16, [], height=2))
    interconnect.add_tile(tile3)
    # now we have the following layout
    # |-0-|-3-|
    # |-2-|-3-|
    # |-2-|-1-|
    # |-2-|-1-|
    # it's full now
    assert not interconnect.has_empty_tile()


def test_uniform():
    # USAGE
    chip_size = 2
    track_width = 16
    num_track = 3
    track_length = 1

    def dummy_col(_: int, __: int):
        return DummyCore()

    in_conn = [(SwitchBoxSide.WEST, SwitchBoxIO.SB_IN),
               (SwitchBoxSide.WEST, SwitchBoxIO.SB_OUT)]
    out_conn = [(SwitchBoxSide.EAST, SwitchBoxIO.SB_OUT),
                (SwitchBoxSide.WEST, SwitchBoxIO.SB_OUT)]
    ic = create_uniform_interconnect(chip_size, chip_size, track_width,
                                     dummy_col,
                                     {"data_in": in_conn,
                                      "data_out": out_conn},
                                     {track_length: num_track},
                                     SwitchBoxType.Disjoint)
    ic.realize()
    # dump the graph
    ic.dump_routing_graph("test.graph")

    # TESTS
    # since we already covered the tests on individual tiles
    # we will focus on the interconnect between each tiles here
    # we first test horizontal connections
    for x in range(0, chip_size - 1):
        for y in range(chip_size):
            tile_from = ic[x, y]
            tile_to = ic[x + track_length, y]
            assert tile_from in ic
            assert tile_to in ic
            for track in range(num_track):
                # get individual sb mux
                tile_from_mux = tile_from.get_sb_circuit(SwitchBoxSide.EAST,
                                                         track,
                                                         SwitchBoxIO.SB_OUT)
                tile_to_mux = tile_to.get_sb_circuit(SwitchBoxSide.WEST,
                                                     track,
                                                     SwitchBoxIO.SB_IN)
                assert_ic_mux_conn(ic, tile_from_mux, tile_to_mux)
                # reverse direction
                tile_from_mux = tile_to.get_sb_circuit(SwitchBoxSide.WEST,
                                                       track,
                                                       SwitchBoxIO.SB_OUT)
                tile_to_mux = tile_from.get_sb_circuit(SwitchBoxSide.EAST,
                                                       track,
                                                       SwitchBoxIO.SB_IN)
                assert_ic_mux_conn(ic, tile_from_mux, tile_to_mux)

    # now for the vertical connections
    for x in range(chip_size):
        for y in range(0, chip_size - 1):
            tile_from = ic[x, y]
            tile_to = ic[x, y + track_length]
            assert tile_from in ic
            assert tile_to in ic
            for track in range(num_track):
                # get individual sb mux
                tile_from_mux = tile_from.get_sb_circuit(SwitchBoxSide.SOUTH,
                                                         track,
                                                         SwitchBoxIO.SB_OUT)
                tile_to_mux = tile_to.get_sb_circuit(SwitchBoxSide.NORTH,
                                                     track,
                                                     SwitchBoxIO.SB_IN)
                assert_ic_mux_conn(ic, tile_from_mux, tile_to_mux)
                # reverse direction
                tile_from_mux = tile_to.get_sb_circuit(SwitchBoxSide.NORTH,
                                                       track,
                                                       SwitchBoxIO.SB_OUT)
                tile_to_mux = tile_from.get_sb_circuit(SwitchBoxSide.SOUTH,
                                                       track,
                                                       SwitchBoxIO.SB_IN)
                assert_ic_mux_conn(ic, tile_from_mux, tile_to_mux)


def assert_ic_mux_conn(ic, tile_from_mux, tile_to_mux):
    assert tile_from_mux in ic
    assert tile_to_mux in ic
    # test the connectivity on the graph level
    assert ic.is_connected(tile_from_mux, tile_to_mux)
    # test the actual wire connections
    # Note:
    # the interconnect doesn't hold the wires
    found = False
    for wire in tile_from_mux.wires:
        for conn in wire:
            if conn.owner() == tile_to_mux.mux:
                found = True
                break
    assert found

    # because for each tile_to_mux, we will have exactly one connection,
    # the mux height will be 1
    assert tile_to_mux.mux.height == 1
