from io_core.io_core_magma import IOCore
from memory_core.memory_core_magma import MemCore
from canal.interconnect import Interconnect
import magma
from gemstone.common.transform import pass_signal_through

# This pass creates an extra port to pass clock signals through
# CGRA tiles in the interconnect. This allows us to pass the clock
# signal through the tile without going through the tile's clock tree.

#            clk                         clk   pt_clk
#      ---------------                ---------------
#      |      |      |        \       |   |      |  |
#      |    |---|    |         \      | |---|    |  |
#      |   |-| |-|   |   -------\     ||-| |-|   |  |
#      |       |     |   -------/     |          |  |
#      |       |     |         /      |      ----|  |
#      |       |     |        /       |      |   |  |
#      ---------------                ---------------
#           clk_out                    clk_out  pt_clk_out  
#

def clk_physical(interconnect: Interconnect):
    for (x, y) in interconnect.tile_circuits:
        tile = interconnect.tile_circuits[(x, y)]
        tile_core = tile.core
        # We only want to do this on PE and memory tiles
        if isinstance(tile_core, IOCore) or tile_core is None:
            continue
        elif isinstance(tile_core, MemCore):
            if (x, y+1) in interconnect.tile_circuits:
                tile_below = interconnect.tile_circuits[(x, y+1)]
                if "clk" in tile_below.ports:
                    interconnect.remove_wire(tile.ports.clk_out,
                                             tile_below.ports.clk)
            tile.remove_port("clk_out")
            # Get the PE tile to the left of this mem tile
            tile_left = interconnect.tile_circuits[(x-1, y)]
            # Connect the clk input of this mem tile to the right clk 
            # output of the neighboring PE tile
            interconnect.wire(tile_left.ports.clk_pass_through_out_right,
                              tile.ports.clk)
        else:
            orig_in_port = tile.ports.clk
            orig_out_port = tile.ports.clk_out
            # Remove the pass through connection that already exists
            tile.remove_wire(orig_in_port, orig_out_port)
            # Create a new pass through clock input
            tile.add_port("clk_pass_through", magma.In(magma.Clock))
            pass_through_input = tile.ports.clk_pass_through
            # Create 2 new clk pass through outputs (bottom and right)
            tile.add_port("clk_pass_through_out_bot", magma.Out(magma.Clock))
            tile.add_port("clk_pass_through_out_right", magma.Out(magma.Clock))
            tile.wire(tile.ports.clk_pass_through,
                      tile.ports.clk_pass_through_out_bot)
            tile.wire(tile.ports.clk_pass_through,
                      tile.ports.clk_pass_through_out_right)

            # Connect new clk pass through input to old pass through output
            tile.wire(pass_through_input, orig_out_port)
            # For top row tiles, connect new clk input to global clock
            if y < 2:
                interconnect.wire(interconnect.ports.clk,
                                  pass_through_input)
            # For other tiles, connect new clk input to 
            # pass through output of tile above.
            else:
                tile_above = interconnect.tile_circuits[(x, y-1)]
                interconnect.wire(tile_above.ports.clk_pass_through_out_bot,
                                  pass_through_input)

    
