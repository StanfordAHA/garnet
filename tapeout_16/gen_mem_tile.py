import magma
from tile.tile_magma import Tile
from memory_core.memory_core_magma import MemCore


core = MemCore(16, 1024)
tile = Tile(core)
tile_circ = tile.circuit()
magma.compile("MemTile", tile_circ, output="coreir-verilog")
