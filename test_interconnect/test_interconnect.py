from interconnect.interconnect import Interconnect, InterconnectType
from interconnect.interconnect import Tile, Switch, SwitchManager


def test_switch_manager():
    sb_manager = SwitchManager()
    sb1 = sb_manager.create_disjoint_switch(0, 0, 1, 5)
    sb2 = sb_manager.create_disjoint_switch(0, 1, 1, 5)
    assert sb1.id == sb2.id
    # different ones
    sb3 = sb_manager.create_disjoint_switch(0, 2, 1, 1)
    assert sb3.id == sb1.id + 1


def test_tile():
    interconnect = Interconnect(InterconnectType.Mesh)
    sb_manager = SwitchManager()
    sb = sb_manager.create_disjoint_switch(0, 0, 1, 5)
    switch = Switch(sb)
    tile = Tile(0, 0, 1, switch)
    interconnect.add_tile(tile)
    # test add_tile basic
    assert interconnect.get_size() == (1, 1)
    tile = Tile(1, 2, 2, switch)
    interconnect.add_tile(tile)
    # test add_tile scale
    assert interconnect.get_size() == (2, 4)
    # test get tile
    tile_bottom = interconnect.get_tile(1, 3)
    assert tile_bottom == tile
    # test check empty
    assert interconnect.has_empty_tile()
