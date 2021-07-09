from io_core.io_core_magma import IOCoreBase
from memory_core.memory_core_magma import MemCore
from canal.interconnect import Interconnect
import magma
from gemstone.common.transform import pass_signal_through

# This pass modifies the mesochronous "river routed" clock network
# that Canal creates by default to make it more feasible to meet
# timing requirements.

# Transformations:
# 1. PE tile pass throughs:
# Creates an extra input port on pe tiles called clk_pass_through 
# which is used only to pass clock signals through to adjacent 
# CGRA tiles in the interconnect. 
# This allows us to pass the clock signal through the tile without going
# through the tile's clock tree.
#
# We create 2 pass through clk outputs so that the clk will be passed to
# the tile below and to the tile on right. The right pass through will
# only actually be used when the pe tile is adjacent to a memory tile on the
# right.

#            clk                         clk   pt_clk
#      ---------------                ----------------
#      |      |      |        \       |   |      |   |
#      |    |---|    |         \      | |---|    |   |
#      |   |-| |-|   |   -------\     ||-| |-|   |---| pt_clk_out_right (to mem)
#      |       |     |   -------/     |          |   |
#      |       |     |         /      |      ----|   |
#      |       |     |        /       |      |   |   |
#      ---------------                ----------------
#           clk_out                    clk_out  pt_clk_out_bot  
#
#
#
# 2. No memory clk_passthroughs:
# Gets rid of clk_out clk pass through in memory tiles. All memory tile clk
# inputs will now be driven by left-adjacent PE Tiles. This prevents us from
# having to balance clk pass through delays between PE and memory tiles, which
# frequently required manual post-P&R intervention.

def clk_physical(interconnect: Interconnect):
    for (x, y) in interconnect.tile_circuits:
        tile = interconnect.tile_circuits[(x, y)]
        tile_core = tile.core
        # We only want to do this on PE and memory tiles
        if tile_core is None or isinstance(tile_core, IOCoreBase):
            continue
        elif isinstance(tile_core, MemCore):
            if (x, y+1) in interconnect.tile_circuits:
                tile_below = interconnect.tile_circuits[(x, y+1)]
                if isinstance(tile_below.core, MemCore):
                    interconnect.remove_wire(tile.ports.clk_out,
                                             tile_below.ports.clk)
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
            tile.add_port("clk_pass_through", magma.In(magma.Bit))
            pass_through_input = tile.ports.clk_pass_through
            pass_through_input_as_clk = tile.convert(
                pass_through_input, magma.clock)
            # Create 2 new clk pass through outputs (bottom and right)
            tile.add_port("clk_pass_through_out_bot", magma.Out(magma.Bit))
            tile.add_port("clk_pass_through_out_right", magma.Out(magma.Clock))
            tile.wire(tile.ports.clk_pass_through,
                      tile.ports.clk_pass_through_out_bot)
            tile.wire(pass_through_input_as_clk,
                      tile.ports.clk_pass_through_out_right)

            # Connect new clk pass through input to old pass through output
            tile.wire(pass_through_input_as_clk, orig_out_port)
            # For top row tiles, connect new clk input to global clock
            if y < 2:
                interconnect_clk_as_bit = interconnect.convert(
                    interconnect.ports.clk, magma.bit)
                interconnect.wire(interconnect_clk_as_bit, pass_through_input)
            # For other tiles, connect new clk input to 
            # pass through output of tile above.
            else:
                tile_above = interconnect.tile_circuits[(x, y-1)]
                interconnect.wire(tile_above.ports.clk_pass_through_out_bot,
                                  pass_through_input)

    
