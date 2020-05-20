#========================================================================
# additional-path-groups.tcl
#========================================================================
# The default init step creates path groups to prioritize timing paths.
# This script is designed to be run after that script to add additonal
# path group related constraints.
#
# Author : Alex Carsello
# Date   : May 12, 2020


# For CGRA tiles, the timing of pass through signals
# (clk, reset, config, stall) is very important

set pt_inputs [get_ports {clk_pass_through reset stall config_config*}]
set pt_outputs [get_ports {clk*out reset_out stall_out config_out*}]

group_path -name CriticalPassThrough -from $pt_inputs -to $pt_outputs

setPathGroupOptions CriticalPassThrough -effortLevel high

