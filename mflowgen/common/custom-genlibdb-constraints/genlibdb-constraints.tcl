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

# These RMUX instances have been marked dont_touch
# in the synthesis constraints so we can more easily
# do set_case_analysis on them here
set rmuxes [get_cells -hier -regexp .*RMUX_.*_sel_(inst0|value)]
set rmux_outputs [get_pins -of_objects $rmuxes -filter "direction==out"]
set_case_analysis 1 $rmux_outputs

