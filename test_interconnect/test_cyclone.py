"""Because the majority of Cyclone's functionality has already been tested in
test_circuit.py, we will focus on functions have not been fully tested yet """
from interconnect.cyclone import SwitchBoxSide, Switch, SwitchBoxIO
from interconnect.cyclone import SwitchBoxNode
from interconnect.sb import SwitchBoxHelper


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
    switch = Switch(x, y, num_tracks, bit_width, wires)
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
