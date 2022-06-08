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
set_dont_touch [get_nets ext_tx_outp]  true ; # dragonphy2 11/2020
set_dont_touch [get_nets ext_tx_outn]  true ; # dragonphy2 11/2020

# Genus-specific constraints to prevent these pins from being tied to 0
set_attribute skip_pin_for_undriven_handling true [get_pins -hier *ext_clk_async_p]
set_attribute skip_pin_for_undriven_handling true [get_pins -hier *ext_clk_async_n]
set_attribute skip_pin_for_undriven_handling true [get_pins -hier *ext_clkn]
set_attribute skip_pin_for_undriven_handling true [get_pins -hier *ext_clkp]
set_attribute skip_pin_for_undriven_handling true [get_pins -hier *ext_Vcm]
set_attribute skip_pin_for_undriven_handling true [get_pins -hier *ext_Vcal]
set_attribute skip_pin_for_undriven_handling true [get_pins -hier *ext_mdll_clk_refp]
set_attribute skip_pin_for_undriven_handling true [get_pins -hier *ext_mdll_clk_refn]
set_attribute skip_pin_for_undriven_handling true [get_pins -hier *ext_mdll_clk_monp]
set_attribute skip_pin_for_undriven_handling true [get_pins -hier *ext_mdll_clk_monn]
set_attribute skip_pin_for_undriven_handling true [get_pins -hier *ext_rx_inp]
set_attribute skip_pin_for_undriven_handling true [get_pins -hier *ext_rx_inn]
set_attribute skip_pin_for_undriven_handling true [get_pins -hier *ext_rx_inp_test]
set_attribute skip_pin_for_undriven_handling true [get_pins -hier *ext_rx_inn_test]
set_attribute skip_pin_for_undriven_handling true [get_pins -hier *clk_out_p]
set_attribute skip_pin_for_undriven_handling true [get_pins -hier *clk_out_n]
set_attribute skip_pin_for_undriven_handling true [get_pins -hier *clk_trig_p]
set_attribute skip_pin_for_undriven_handling true [get_pins -hier *clk_trig_n]
set_attribute skip_pin_for_undriven_handling true [get_pins -hier *ext_tx_outp] ; # dragonphy2 11/2020
set_attribute skip_pin_for_undriven_handling true [get_pins -hier *ext_tx_outn] ; # dragonphy2 11/2020
