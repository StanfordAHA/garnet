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

# These SB_IN to SB_OUT combinational paths
# create a loop in the tile_array level
# (dangerous: only disable these during libdb generation)
set_false_path -from [get_ports *SB_IN* -filter {direction == in}] -to [get_ports *SB_OUT* -filter {direction == out}]
