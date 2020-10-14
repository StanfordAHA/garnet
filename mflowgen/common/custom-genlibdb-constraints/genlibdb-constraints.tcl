#====================================================================
# genlibdb-constraints.tcl
#====================================================================
# These constraints are passed to Primetime for both the PE and
# memory tiles in order to activate all of the pipeline registers
# in the tile interconnect. This prevents all downstream tools
# from analyzing combinational loops that can be realized
# in the interconnect.
#
# Authors: Alex Carsello, Teguh Hofstee
# Date: 1/24/2020

# How many tracks per side?
set num_tracks 5
set num_sides 4
# Which is the first bit which controls pipeline registers
set min_bit 0
# One control bit ber routing track
set num_bits [expr $num_tracks * $num_sides]
# Name of SB where the config regs we're targeting reside
set SB_name SB_ID0_${num_tracks}TRACKS_B*
# name of config reg within SB
set config_reg_name config_reg_0

for {set bit $min_bit} {[expr $bit - $min_bit] < $num_bits} {incr bit} {
    # Name of config register in netlist
    if {$::env(flatten_effort) == 0} {
      # When we don't flatten, the config reg is buried under multiple levels of hierarchy
      set config_regs [get_cells ${SB_name}/${config_reg_name}/*/*/*[$bit] -filter "is_sequential==True"]
    } else {
      # When we flatten, we don't need slashes since there is no hierarchy
      set config_regs [get_cells -hierarchical *${SB_name}*${config_reg_name}_Register*[$bit] -filter "is_sequential==True"]
    }
    set config_reg_outs [get_pins -of_objects $config_regs -filter "direction==out"]
    # Set config reg values to 1 so that all pipeline regs are activated
    set_case_analysis 1 $config_reg_outs
}

