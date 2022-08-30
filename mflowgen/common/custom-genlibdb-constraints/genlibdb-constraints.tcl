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

# Need to set interactive constraint mode when using
# Innovus to generate .lib files
#set_interactive_constraint_modes [all_constraint_modes]

# These RMUX instances have been marked dont_touch
# in the synthesis constraints so we can more easily
# do set_case_analysis on them here
set rmuxes [get_cells -hier -regexp .*RMUX_.*_sel_(inst0|value)]
set rmux_outputs [get_pins -of_objects $rmuxes -filter "direction==out"]
set_case_analysis 1 $rmux_outputs

# set Fifo enable low
set fifo_regs [get_cells -hier *REG*fifo_value]
set fifo_reg_outputs [get_pins -of_objects $fifo_regs -filter "direction==out"]
set_case_analysis 0 $fifo_reg_outputs

# set Fifo start high
set fifo_regs [get_cells -hier *REG*start_value]
set fifo_reg_outputs [get_pins -of_objects $fifo_regs -filter "direction==out"]
set_case_analysis 1 $fifo_reg_outputs

# set Fifo value high
set fifo_regs [get_cells -hier *REG*end_value]
set fifo_reg_outputs [get_pins -of_objects $fifo_regs -filter "direction==out"]
set_case_analysis 1 $fifo_reg_outputs

