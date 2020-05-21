#-----------------------------------------------------------------------------
# TCL Script
#-----------------------------------------------------------------------------
# Purpose: Constraints for paths between CGRA tile array, GLB, GLC
#------------------------------------------------------------------------------
#
# Author   : Alex Carsello
# Date     : May 18, 2020
#------------------------------------------------------------------------------

#set_multicycle_path 5 -setup -to [get_pins -hier *global_controller*/cgra_cfg_rd_data*]
#set_multicycle_path 4 -hold -to [get_pins -hier *global_controller*/cgra_cfg_rd_data*]

# Setting this to be a false path instead because the tile array.lib file
# we generate for some reason reports this path to have huge negative delay,
# which causes major hold time issues
set_false_path -to [get_pins -hier *global_controller*/cgra_cfg_rd_data*]

