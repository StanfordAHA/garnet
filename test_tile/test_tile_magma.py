from test_tile.dummy_core_magma import DummyCore
import magma
from bit_vector import BitVector
from tile.tile_magma import Tile
from common.testers import ResetTester, ConfigurationTester


def test_tile():
    core = DummyCore(5, 16)
    tile = Tile(core)
    magma.compile(f"test_tile/build/{tile.name}", tile,
                  output="coreir-verilog")
