import magma
from tile.tile_magma import Tile
from pe_core.pe_core_magma import PECore


core = PECore()
tile = Tile(core)
pass_throughs = [tile.ports.clk, tile.ports.reset,
                 tile.ports.stall, tile.ports.config]
for signal in pass_throughs:
    tile.pass_signal_through(signal)
tile.read_data_reduction()
tile_circ = tile.circuit()
magma.compile("PETile", tile_circ, output="coreir-verilog")
