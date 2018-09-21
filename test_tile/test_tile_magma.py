from common.dummy_core_magma import DummyCore
import magma
from bit_vector import BitVector
from tile.tile_magma import Tile
from common.testers import ResetTester, ConfigurationTester


def test_tile():
    core = DummyCore()
    tile = Tile(core)
    tile_circ = tile.circuit()
    magma.compile(f"{tile.name}", tile_circ,
                  output="coreir-verilog")
