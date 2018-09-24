from common.dummy_core_magma import DummyCore
import magma
from bit_vector import BitVector
from tile.tile_magma import Tile
from common.testers import BasicTester
import tempfile
from fault.random import random_bv


def test_tile():
    core = DummyCore()
    tile = Tile(core)
    tile_circ = tile.circuit()
    # No functional model for tile yet, so we have to use the
    # standard fault tester for now
    tester = BasicTester(tile_circ, tile_circ.clk, tile_circ.reset)
    # assign the tile a random ID for configuration
    tile_id = random_bv(16)
    tester.poke(tile_circ.tile_id, tile_id)

    with tempfile.TemporaryDirectory() as tempdir:
        tester.compile_and_run(target="verilator",
                               magma_output="coreir-verilog",
                               directory=tempdir,
                               flags=["-Wno-fatal"])
