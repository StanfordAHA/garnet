import magma
from tile.tile_magma import Tile
from memory_core.memory_core_magma import MemCore
from interconnect.interconnect_magma import Interconnect
from column.column_magma import ColumnMeso
from tile.tile_magma import Tile


width = 2
height = 2
columns = []
for i in range(width):
    tiles = []
    for j in range(height):
        core = MemCore(16, 1024)
        tiles.append(Tile(core))
    columns.append(ColumnMeso(tiles))
tile_grid = Interconnect(columns)

tile_grid_circ = tile_grid.circuit()
magma.compile("TileGrid", tile_grid_circ, output="coreir-verilog")
