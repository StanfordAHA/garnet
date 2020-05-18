#-----------------------------------------------------------------------------
# TCL Script
#-----------------------------------------------------------------------------
# Purpose: Constraints for paths between CGRA tile array, GLB, GLC
#------------------------------------------------------------------------------
#
# Author   : Alex Carsello
# Date     : May 18, 2020
#------------------------------------------------------------------------------

set_multicycle_path 5 -setup -to [get_pins -hier *global_controller*/cgra_cfg_rd_data*]
set_multicycle_path 4 -hold -to [get_pins -hier *global_controller*/cgra_cfg_rd_data*]

