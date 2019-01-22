"""Because the majority of Cyclone's functionality has already been tested in
test_circuit.py, we will focus on functions have not been fully tested yet """
from interconnect.cyclone import *
from common.dummy_core_magma import DummyCore
from interconnect.util import create_uniform_interconnect, SwitchBoxType
import pytest


def test_remove_side_sb():
    """test remove the entire side of a switch. it's useful to create a tile
    that has a side missing, such as a tall memory tile
    """
    # USAGE:
    bit_width = 16
    num_tracks = 5
    x = 0
    y = 0

    wires = SwitchBoxHelper.get_disjoint_sb_wires(num_tracks)
    switch = SwitchBox(x, y, num_tracks, bit_width, wires)
    switch.remove_side_sbs(SwitchBoxSide.NORTH, SwitchBoxIO.SB_IN)

    # TESTS
    # we will get an index error if we tries to access the deleted nodes
    try:
        _ = switch[SwitchBoxSide.NORTH, 0, SwitchBoxIO.SB_IN]
        assert False
    except IndexError:
        pass
    # now test the connection to see if there is any
    all_sbs = switch.get_all_sbs()
    for sb in all_sbs:
        side_is_north = sb.side == SwitchBoxSide.NORTH
        io_is_in = sb.io == SwitchBoxIO.SB_IN
        assert not (side_is_north and io_is_in)
        for node in sb:
            side_is_north = node.side == SwitchBoxSide.NORTH
            io_is_in = node.io == SwitchBoxIO.SB_IN
            assert not (side_is_north and io_is_in)

        for node in sb.get_conn_in():   # type: SwitchBoxNode
            # override the type hints here since we don't have any other
            # connections
            side_is_north = node.side == SwitchBoxSide.NORTH
            io_is_in = node.io == SwitchBoxIO.SB_IN
            assert not (side_is_north and io_is_in)

    # one remove one side one io, so the total number of sbs left is
    # (2 * 4 - 1) * num_tracks
    assert len(all_sbs) == (2 * 4 - 1) * num_tracks


def test_tiling():
    """test low-level tiling. we expect the tiling be handled internally.
    as a result, users do not need to create a graph tile by hand
    """
    width = 16
    interconnect = InterconnectGraph(width)
    tile1 = Tile.create_tile(0, 0, 1, 16, [])
    interconnect.add_tile(tile1)
    # now we have the following layout
    # |-0-|
    assert interconnect.get_size() == (1, 1)

    tile2 = Tile.create_tile(1, 2, 1, 16, [], height=2)
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
    tile2 = Tile.create_tile(0, 1, 1, 16, [], height=3)
    interconnect.add_tile(tile2)
    # now we have the following layout
    # |-0-|---|
    # |-2-|---|
    # |-2-|-1-|
    # |-2-|-1-|
    tile3 = Tile.create_tile(1, 0, 1, 16, [], height=2)
    interconnect.add_tile(tile3)
    # now we have the following layout
    # |-0-|-3-|
    # |-2-|-3-|
    # |-2-|-1-|
    # |-2-|-1-|
    # it's full now
    assert not interconnect.has_empty_tile()


def test_policy_ignore():
    """test low-level interconnect policy based connection"""
    width = 16
    num_track = 1
    wire_length = 2

    disjoint_wires = SwitchBoxHelper.get_disjoint_sb_wires(1)

    interconnect = InterconnectGraph(width)
    tile0 = Tile.create_tile(0, 0, width, num_track, disjoint_wires)
    interconnect.add_tile(tile0)
    tile1 = Tile.create_tile(2, 3, width, num_track, disjoint_wires)
    interconnect.add_tile(tile1)
    tile2 = Tile.create_tile(0, 2, width, num_track, disjoint_wires)
    interconnect.add_tile(tile2)
    tile3 = Tile.create_tile(2, 0, width, num_track, disjoint_wires)
    interconnect.add_tile(tile3)
    tile4 = Tile.create_tile(0, 4, width, num_track, disjoint_wires)
    interconnect.add_tile(tile4)
    tile5 = Tile.create_tile(4, 4, width, num_track, disjoint_wires)
    interconnect.add_tile(tile5)

    # USAGE
    interconnect.connect_switchbox(0, 0, 5, 5, wire_length, num_track - 1,
                                   InterconnectPolicy.Ignore)

    # we now have this following layout
    # |-0-|---|-3-|---|---|
    # |---|---|---|---|---|
    # |-2-|---|---|---|---|
    # |---|---|-1-|---|---|
    # |-4-|---|---|---|-5-|
    # TESTS
    assert interconnect.get_size() == (5, 5)
    # test connections
    # 3 <-> 1
    sb_from = tile0.get_sb(SwitchBoxSide.SOUTH, 0, SwitchBoxIO.SB_OUT)
    sb_to = tile2.get_sb(SwitchBoxSide.NORTH, 0, SwitchBoxIO.SB_IN)
    assert sb_to in sb_from

    sb_from = tile0.get_sb(SwitchBoxSide.EAST, 0, SwitchBoxIO.SB_OUT)
    sb_to = tile3.get_sb(SwitchBoxSide.WEST, 0, SwitchBoxIO.SB_IN)
    assert sb_to in sb_from

    sb_from = tile3.get_sb(SwitchBoxSide.SOUTH, 0, SwitchBoxIO.SB_OUT)
    sb_to = tile1.get_sb(SwitchBoxSide.NORTH, 0, SwitchBoxIO.SB_IN)
    assert sb_to not in sb_from

    sb_from = tile4.get_sb(SwitchBoxSide.EAST, 0, SwitchBoxIO.SB_OUT)
    sb_to = tile5.get_sb(SwitchBoxSide.WEST, 0, SwitchBoxIO.SB_IN)
    assert sb_to not in sb_from


def test_policy_pass_through():
    """test low-level interconnect policy based connection"""
    width = 16
    num_track = 1
    wire_length = 2

    disjoint_wires = SwitchBoxHelper.get_disjoint_sb_wires(1)

    interconnect = InterconnectGraph(width)
    tile0 = Tile.create_tile(0, 0, width, num_track, disjoint_wires)
    interconnect.add_tile(tile0)
    tile1 = Tile.create_tile(2, 3, width, num_track, disjoint_wires)
    interconnect.add_tile(tile1)
    tile2 = Tile.create_tile(0, 2, width, num_track, disjoint_wires)
    interconnect.add_tile(tile2)
    tile3 = Tile.create_tile(2, 0, width, num_track, disjoint_wires)
    interconnect.add_tile(tile3)
    tile4 = Tile.create_tile(0, 4, width, num_track, disjoint_wires)
    interconnect.add_tile(tile4)
    tile5 = Tile.create_tile(4, 4, width, num_track, disjoint_wires)
    interconnect.add_tile(tile5)

    # USAGE
    interconnect.connect_switchbox(0, 0, 5, 5, wire_length, num_track - 1,
                                   InterconnectPolicy.PassThrough)

    # we now have this following layout
    # |-0-|---|-3-|---|---|
    # |---|---|---|---|---|
    # |-2-|---|---|---|---|
    # |---|---|-1-|---|---|
    # |-4-|---|---|---|-5-|
    # TESTS
    assert interconnect.get_size() == (5, 5)
    # test connections
    sb_from = tile3.get_sb(SwitchBoxSide.SOUTH, 0, SwitchBoxIO.SB_OUT)
    sb_to = tile1.get_sb(SwitchBoxSide.NORTH, 0, SwitchBoxIO.SB_IN)
    assert sb_to in sb_from

    sb_from = tile4.get_sb(SwitchBoxSide.EAST, 0, SwitchBoxIO.SB_OUT)
    sb_to = tile5.get_sb(SwitchBoxSide.WEST, 0, SwitchBoxIO.SB_IN)
    assert sb_to in sb_from


def assert_tile_coordinate(tile: Tile, x: int, y: int):
    assert tile.x == x and tile.y == y
    for sb in tile.switchbox.get_all_sbs():
        assert_coordinate(sb, x, y)
    for _, node in tile.ports.items():
        assert_coordinate(node, x, y)
    for _, node in tile.registers:
        assert_coordinate(node, x, y)


def assert_coordinate(node: Node, x: int, y: int):
    assert node.x == x and node.y == y


@pytest.mark.parametrize("chip_size", [2, 4])
@pytest.mark.parametrize("num_track", [2, 5])
@pytest.mark.parametrize("track_width", [1, 16])
def test_uniform(chip_size: int, num_track: int, track_width):
    # USAGE
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

    # TESTS
    for x in range(chip_size):
        for y in range(chip_size):
            assert_tile_coordinate(ic[x, y], x, y)
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
                tile_from_sb = tile_from.get_sb(SwitchBoxSide.EAST,
                                                track,
                                                SwitchBoxIO.SB_OUT)
                tile_to_sb = tile_to.get_sb(SwitchBoxSide.WEST,
                                            track,
                                            SwitchBoxIO.SB_IN)
                assert tile_from_sb in ic and tile_to_sb in ic
                assert tile_to_sb in tile_from_sb
                # reverse direction
                tile_from_sb = tile_to.get_sb(SwitchBoxSide.WEST,
                                              track,
                                              SwitchBoxIO.SB_OUT)
                tile_to_sb = tile_from.get_sb(SwitchBoxSide.EAST,
                                              track,
                                              SwitchBoxIO.SB_IN)
                assert tile_from_sb in ic and tile_to_sb in ic
                assert tile_to_sb in tile_from_sb

    # now for the vertical connections
    for x in range(chip_size):
        for y in range(0, chip_size - 1):
            tile_from = ic[x, y]
            tile_to = ic[x, y + track_length]
            assert tile_from in ic
            assert tile_to in ic
            for track in range(num_track):
                # get individual sb mux
                tile_from_sb = tile_from.get_sb(SwitchBoxSide.SOUTH,
                                                track,
                                                SwitchBoxIO.SB_OUT)
                tile_to_sb = tile_to.get_sb(SwitchBoxSide.NORTH,
                                            track,
                                            SwitchBoxIO.SB_IN)
                assert tile_from_sb in ic and tile_to_sb in ic
                assert tile_to_sb in tile_from_sb
                # reverse direction
                tile_from_sb = tile_to.get_sb(SwitchBoxSide.NORTH,
                                              track,
                                              SwitchBoxIO.SB_OUT)
                tile_to_sb = tile_from.get_sb(SwitchBoxSide.SOUTH,
                                              track,
                                              SwitchBoxIO.SB_IN)
                assert tile_from_sb in ic and tile_to_sb in ic
                assert tile_to_sb in tile_from_sb
