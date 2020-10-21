from io_core.io_core_magma import IOCoreValid
from canal.interconnect import Interconnect
import magma
from gemstone.generator.const import Const
from hwtypes import BitVector

# We create constant tie hi and tie lo outputs on each tile
# These pins will be interleaved with the tile_id pins as follows
# | hi[0] | id[0] | lo[0] | id[1] | hi[1] | id[2] | lo[1] | id[3] | hi[2] | ...
# We are doing this so that we can actually connect the tile_id inputs
# to the proper constant values without uniquifying the tiles and while
# maintaining our abutted array of tile hard macros

def tile_id_physical(interconnect: Interconnect):
    tile_id_width = interconnect.tile_id_width
    tie_hi_width = (tile_id_width // 2) + 1
    if (tile_id_width % 2) == 0 :
        tie_lo_width = tile_id_width // 2
    else:
        tie_lo_width = (tile_id_width // 2) + 1
    for (x, y) in interconnect.tile_circuits:
        tile = interconnect.tile_circuits[(x, y)]
        tile_core = tile.core
        if isinstance(tile_core, IOCoreValid) or tile_core is None:
            continue
        tile.add_ports(
            hi=magma.Out(magma.Bits[tie_hi_width]),
            lo=magma.Out(magma.Bits[tie_lo_width])
        )
        # wire all hi bits high
        tile.wire(tile.ports.hi, Const((2 ** tie_hi_width) - 1))
        # wire all lo bits low
        tile.wire(tile.ports.lo, Const(0))
        # Get the correct tile_id value
        x_bv = BitVector[tile_id_width / 2](x)
        y_bv = BitVector[tile_id_width / 2](y)
        tile_id_bv = BitVector.concat(y_bv, x_bv)
        # Disconnect existing constant from tile_id port
        tile_id_port = tile.ports.tile_id
        for wire in interconnect.wires:
            if tile_id_port in wire:
                interconnect.remove_wire(wire[0], wire[1])
                break

        # Actually connect hi/lo outputs to tile_id at top level
        for i in range(tile_id_width):
            lo_index = i // 2
            if (i % 2) == 0:
                hi_index = i // 2
            else:
                hi_index = (i // 2) + 1
            hi_port = tile.ports.hi[hi_index]
            lo_port = tile.ports.lo[lo_index]
            tie_port = hi_port if (tile_id_bv[i] == 1) else lo_port
            # Connect tile_id ports to hi/lo outputs instead of constant
            interconnect.wire(tile.ports.tile_id[i], tie_port)
