from io_core.io_core_magma import IOCore
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
        orig_in_port = tile.ports.clk
        orig_out_port = tile.ports.clk_out
        # Remove the pass through connection that already exists
        tile.remove_wire(orig_in_port, orig_out_port)
        # Create a new pass through clock input
        tile.add_port("clk_pass_through", magma.In(magma.Clock))
        pass_through_input = tile.ports.clk_pass_through
        # Create new pass through output
        pass_through_output = pass_signal_through(tile, pass_through_input)
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
            interconnect.wire(tile_above.ports.clk_pass_through_out,
                              pass_through_input)
       
        
    
