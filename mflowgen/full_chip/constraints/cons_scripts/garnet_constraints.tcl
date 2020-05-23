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

set_multicycle_path 5 -setup -through [get_pins -hier *GlobalBuffer*/*interrupt_pulse*]
set_multicycle_path 4 -hold  -through [get_pins -hier *GlobalBuffer*/*interrupt_pulse*]

# Dont touch analog nets for dragonphy

set_dont_touch [get_nets ext_clk_async_p]  true
set_dont_touch [get_nets ext_clk_async_n]  true
set_dont_touch [get_nets ext_clkn]  true
set_dont_touch [get_nets ext_clkp]  true
set_dont_touch [get_nets ext_Vcm]  true
set_dont_touch [get_nets ext_Vcal]  true
set_dont_touch [get_nets ext_mdll_clk_refp]  true
set_dont_touch [get_nets ext_mdll_clk_refn]  true
set_dont_touch [get_nets ext_mdll_clk_monp]  true
set_dont_touch [get_nets ext_mdll_clk_monn]  true
set_dont_touch [get_nets ext_rx_inp]  true
set_dont_touch [get_nets ext_rx_inn]  true
set_dont_touch [get_nets ext_rx_inp_test]  true
set_dont_touch [get_nets ext_rx_inn_test]  true
set_dont_touch [get_nets clk_out_p]  true
set_dont_touch [get_nets clk_out_n]  true
set_dont_touch [get_nets clk_trig_p]  true
set_dont_touch [get_nets clk_trig_n]  true
