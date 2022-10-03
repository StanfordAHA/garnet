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
set_multicycle_path 10 -setup -through [get_pins -hier *global_controller*/cgra_cfg_rd_data*]
set_multicycle_path 9 -hold -through [get_pins -hier *global_controller*/cgra_cfg_rd_data*]

set_multicycle_path 10 -setup -through [get_pins -hier *global_controller*/sram_cfg_rd_data*]
set_multicycle_path 9 -hold -through [get_pins -hier *global_controller*/sram_cfg_rd_data*]

#set_multicycle_path 3 -setup -through [get_pins -hier *global_controller*/glb_cfg_rd_data*]
#set_multicycle_path 2 -hold -through [get_pins -hier *global_controller*/glb_cfg_rd_data*]

set_multicycle_path 5 -setup -through [get_pins -hier *global_buffer*/*interrupt_pulse*]
set_multicycle_path 4 -hold  -through [get_pins -hier *global_buffer*/*interrupt_pulse*]
set_multicycle_path -setup 10 -to [get_pins -hier global_buffer/pcfg_broadcast_stall*]
set_multicycle_path -hold 9 -to [get_pins -hier global_buffer/pcfg_broadcast_stall*]
set_multicycle_path -setup 10 -to [get_pins -hier global_buffer/glb_clk_en_master*]
set_multicycle_path -hold 9 -to [get_pins -hier global_buffer/glb_clk_en_master*]
set_multicycle_path -setup 10 -to [get_pins -hier global_buffer/glb_clk_en_bank_master*]
set_multicycle_path -hold 9 -to [get_pins -hier global_buffer/glb_clk_en_bank_master*]
set_multicycle_path -setup 10 -to [get_pins -hier global_buffer/flush_crossbar_sel*]
set_multicycle_path -hold 9 -to [get_pins -hier global_buffer/flush_crossbar_sel*]

# Don't consider xgcd timing since it's not done yet.
set_false_path -through [get_cells -hier u_xgcd_wrapper_top]
set_false_path -from [get_pins -hier u_xgcd_wrapper_top/clk_div_8]
set_false_path -to [get_pins -hier u_xgcd_wrapper_top/clk_div_8]
set_false_path -through [get_pins -hier u_xgcd_wrapper_top/clk_div_8]

set_false_path -to [get_clocks xgcd_div8_clk]
set_false_path -from [get_clocks xgcd_div8_clk]
