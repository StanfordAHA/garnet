#-----------------------------------------------------------------------------
# TCL Script
#-----------------------------------------------------------------------------
# Purpose: Constraints for paths between CGRA tile array, GLB, GLC
#------------------------------------------------------------------------------
#
# Author   : Alex Carsello
# Date     : May 18, 2020
#------------------------------------------------------------------------------

# Paths involved with reading configuration data can be relaxed
set_multicycle_path 10 -setup -to [get_pins -hier *global_controller*/cgra_cfg_rd_data*]
set_multicycle_path 9 -hold -to [get_pins -hier *global_controller*/cgra_cfg_rd_data*]

set_multicycle_path 10 -setup -to [get_pins -hier *global_controller*/sram_cfg_rd_data*]
set_multicycle_path 9 -hold -to [get_pins -hier *global_controller*/sram_cfg_rd_data*]

set_multicycle_path 5 -setup -through [get_pins -hier *global_buffer*/*interrupt_pulse*]
set_multicycle_path 4 -hold  -through [get_pins -hier *global_buffer*/*interrupt_pulse*]


