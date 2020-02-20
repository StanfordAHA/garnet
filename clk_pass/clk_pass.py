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
        if isinstance(tile_core, IOCore) or tile_core is None:
            continue
        orig_in_port = tile.ports.clk
        orig_out_port = tile.ports.clk_out
        tile.remove_wire(orig_in_port, orig_out_port)
        tile.add_port("clk_pass_through", magma.In(magma.Clock))
        pass_through_output = pass_signal_through(tile, tile.ports.pass_through_clk)
        tile.wire(tile.ports.pass_through_clk, orig_out_port)
        if y < 2:
            interconnect.wire(interconnect.ports.clk,
                              tile.ports.pass_through_clk)
        else:
            interconnect.wire(interconnect.tile_circuits[(x, y-1)].ports.pass_through_clk_out,
                              tile.ports.pass_through_clk)
       
        
    
