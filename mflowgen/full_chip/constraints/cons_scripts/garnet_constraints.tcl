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
set_multicycle_path 13 -setup -through [get_pins -hier *global_controller*/cgra_cfg_rd_data*]
set_multicycle_path 12 -hold -through [get_pins -hier *global_controller*/cgra_cfg_rd_data*]

set_multicycle_path 13 -setup -through [get_pins -hier *global_controller*/sram_cfg_rd_data*]
set_multicycle_path 12 -hold -through [get_pins -hier *global_controller*/sram_cfg_rd_data*]

set_multicycle_path 3 -setup -through [get_pins -hier *global_controller*/glb_cfg_rd_data*]
set_multicycle_path 2 -hold -through [get_pins -hier *global_controller*/glb_cfg_rd_data*]

set_multicycle_path 5 -setup -through [get_pins -hier *global_buffer*/*interrupt_pulse*]
set_multicycle_path 4 -hold  -through [get_pins -hier *global_buffer*/*interrupt_pulse*]
set_multicycle_path -setup 13 -to [get_pins -hier global_buffer/pcfg_broadcast_stall*]
set_multicycle_path -hold 12 -to [get_pins -hier global_buffer/pcfg_broadcast_stall*]
set_multicycle_path -setup 13 -to [get_pins -hier global_buffer/glb_clk_en_master*]
set_multicycle_path -hold 12 -to [get_pins -hier global_buffer/glb_clk_en_master*]
set_multicycle_path -setup 13 -to [get_pins -hier global_buffer/glb_clk_en_bank_master*]
set_multicycle_path -hold 12 -to [get_pins -hier global_buffer/glb_clk_en_bank_master*]
set_multicycle_path -setup 13 -to [get_pins -hier global_buffer/flush_crossbar_sel*]
set_multicycle_path -hold 12 -to [get_pins -hier global_buffer/flush_crossbar_sel*]

# Relax tile array and glb reset, stall
set_multicycle_path -setup 3 -through [get_pins -hier global_buffer/reset]
set_multicycle_path -hold 2 -through [get_pins -hier global_buffer/reset]

set_multicycle_path -setup 3 -through [get_pins -hier Interconnect_inst0/reset]
set_multicycle_path -hold 2 -through [get_pins -hier Interconnect_inst0/reset]

set_multicycle_path -setup 3 -through [get_pins -hier Interconnect_inst0/stall*]
set_multicycle_path -hold 2 -through [get_pins -hier Interconnect_inst0/stall*]

set_false_path -from [get_pins -hier *global_controller*/clk_in*] -to [get_pins -hier *global_controller*/tck*]
set_false_path -from [get_pins -hier *global_controller*/tck*]    -to [get_pins -hier *global_controller*/clk_in*]

set_false_path -hold -through [get_property [get_pins -hierarchical */fwen]      full_name]
set_false_path -hold -through [get_property [get_pins -hierarchical */clkbyp]    full_name]
set_false_path -hold -through [get_property [get_pins -hierarchical */mcen]      full_name]
set_false_path -hold -through [get_property [get_pins -hierarchical */mc[0]]     full_name]
set_false_path -hold -through [get_property [get_pins -hierarchical */mc[1]]     full_name]
set_false_path -hold -through [get_property [get_pins -hierarchical */mc[2]]     full_name]
set_false_path -hold -through [get_property [get_pins -hierarchical */wpulseen]  full_name]
set_false_path -hold -through [get_property [get_pins -hierarchical */wpulse[0]] full_name]
set_false_path -hold -through [get_property [get_pins -hierarchical */wpulse[1]] full_name]
set_false_path -hold -through [get_property [get_pins -hierarchical */wa[0]]     full_name]
set_false_path -hold -through [get_property [get_pins -hierarchical */wa[1]]     full_name]

set icg_hack_cells [get_cells -hier -regexp .*u_icg_hack]
set_dont_touch $icg_hack_cells true

set_dont_touch [get_nets pad_diffclkrx_inn]
set_dont_touch [get_nets pad_diffclkrx_inp]
