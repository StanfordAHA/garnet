import magma
from tile.tile_magma import Tile
from pe_core.pe_core_magma import PECore


core = PECore()
tile = Tile(core)
tile_circ = tile.circuit()
magma.compile("PETile", tile_circ, output="coreir-verilog")
