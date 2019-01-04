from interconnect.interconnect import Interconnect, InterconnectType
from interconnect.cyclone import Tile as GTile
from interconnect.cyclone import SwitchBoxSide, SwitchBoxIO
from interconnect.interconnect import create_uniform_interconnect
from interconnect.interconnect import SwitchBoxType, TileCircuit
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
    tile = TileCircuit(GTile.create_tile(0, 0, 1, 16, []))
    interconnect.add_tile(tile)
    # test add_tile basic
    assert interconnect.get_size() == (1, 1)
    tile = TileCircuit(GTile.create_tile(1, 2, 1, 16, [], height=2))
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


def test_uniform():
    chip_width = 2
    track_width = 16

    def dummy_col(x: int, y: int):
        return DummyCore()

    in_conn = [(SwitchBoxSide.WEST, SwitchBoxIO.SB_IN),
               (SwitchBoxSide.WEST, SwitchBoxIO.SB_OUT)]
    out_conn = [(SwitchBoxSide.EAST, SwitchBoxIO.SB_OUT),
                (SwitchBoxSide.WEST, SwitchBoxIO.SB_OUT)]
    ic = create_uniform_interconnect(chip_width, chip_width, track_width,
                                     dummy_col,
                                     {"data_in": in_conn,
                                      "data_out": out_conn},
                                     {1: 3},
                                     SwitchBoxType.Disjoint)
    ic.realize()
