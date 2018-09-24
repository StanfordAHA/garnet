from common.dummy_core_magma import DummyCore
import magma
from bit_vector import BitVector
from tile.tile_magma import Tile
from common.testers import BasicTester
import fault


def test_tile():
    core = DummyCore()
    tile = Tile(core)
    tile_circ = tile.circuit()
    magma.compile(f"{tile.name()}", tile_circ, output="coreir-verilog")

    # No functional model for tile yet, so we have to use the
    # standard fault tester for now
    tester = BasicTester(tile_circ, tile_circ.clk, tile_circ.reset)
