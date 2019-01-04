from interconnect.interconnect import Interconnect, InterconnectType
from interconnect.graph import Switch, Tile
from interconnect.interconnect import SwitchBoxSide, SwitchBoxIO
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


def test_tile():
    width = 16
    interconnect = Interconnect(width, InterconnectType.Mesh)
    switch = Switch(0, 0, 1, 16, [])
    tile = Tile(0, 0, 16, switch)
    interconnect.add_tile(tile)
    # test add_tile basic
    assert interconnect.get_size() == (1, 1)
    tile = Tile(1, 2, 16, switch, height=2)
    interconnect.add_tile(tile)
    # test add_tile scale
    assert interconnect.get_size() == (2, 4)
    # test get tile
    tile_bottom = interconnect.get_tile(1, 3)
    assert tile_bottom == interconnect.get_tile(1, 2)
    assert tile_bottom == tile
    # test check empty
    assert interconnect.has_empty_tile()

    tile.set_core(DummyCore())



test_tile()

