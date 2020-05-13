#=========================================================================
# Design Constraints File
#=========================================================================

# This constraint sets the target clock period for the chip in
# nanoseconds. Note that the first parameter is the name of the clock
# signal in your verlog design. If you called it something different than
# clk you will need to change this. You should set this constraint
# carefully. If the period is unrealistically small then the tools will
# spend forever trying to meet timing and ultimately fail. If the period
# is too large the tools will have no trouble but you will get a very
# conservative implementation.

set clock_net  clk
set clock_name ideal_clock

create_clock -name ${clock_name} \
             -period ${dc_clock_period} \
             [get_ports ${clock_net}]

# This constraint sets the load capacitance in picofarads of the
# output pins of your design.

set_load -pin_load $ADK_TYPICAL_ON_CHIP_LOAD [all_outputs]

# This constraint sets the input drive strength of the input pins of
# your design. We specifiy a specific standard cell which models what
# would be driving the inputs. This should usually be a small inverter
# which is reasonable if another block of on-chip logic is driving
# your inputs.

set_driving_cell -no_design_rule \
  -lib_cell $ADK_DRIVING_CELL [all_inputs]

# set_min_delay for all inputs 
set_min_delay -from [get_ports proc_*i] [expr ${dc_clock_period}*0.55]

# all est<->wst connections
set_input_delay -clock ${clock_name} [expr ${dc_clock_period}*0.4] [get_ports *_esti*]
set_input_delay -clock ${clock_name} [expr ${dc_clock_period}*0.4] [get_ports *_wsti*]
set_input_delay -clock ${clock_name} [expr ${dc_clock_period}*0.4] [get_ports if_cfg_est* -filter "direction==in"]
set_input_delay -clock ${clock_name} [expr ${dc_clock_period}*0.4] [get_ports if_cfg_wst* -filter "direction==in"]
set_input_delay -clock ${clock_name} [expr ${dc_clock_period}*0.4] [get_ports if_sram_cfg_est* -filter "direction==in"]
set_input_delay -clock ${clock_name} [expr ${dc_clock_period}*0.4] [get_ports if_sram_cfg_wst* -filter "direction==in"]
# cfg_clk_en is negative edge triggered
set_input_delay -clock ${clock_name} [expr ${dc_clock_period}*0.4] -clock_fall [get_ports *_clk_en -filter "direction==in"]

# To fix pc_rd_data setup time violation
set_max_delay -to [get_ports pc_rd_data_w2e_esto] [expr ${dc_clock_period}*0.85]
set_max_delay -from [get_ports pc_rd_data_w2e_wsti] [expr ${dc_clock_period}*0.90]

# tile id is constant
set_input_delay -clock ${clock_name} 0 glb_tile_id

# set_output_delay constraints for output ports
# default output delay is 0.2
set_output_delay -clock ${clock_name} [expr ${dc_clock_period}*0.2] [all_outputs]

# all est<->wst connections
set_output_delay -clock ${clock_name} [expr ${dc_clock_period}*0.4] [get_ports *_esto* -filter "direction==out"]
set_output_delay -clock ${clock_name} [expr ${dc_clock_period}*0.4] [get_ports *_wsto* -filter "direction==out"]
set_output_delay -clock ${clock_name} [expr ${dc_clock_period}*0.4] [get_ports if_cfg_est* -filter "direction==out"]
set_output_delay -clock ${clock_name} [expr ${dc_clock_period}*0.4] [get_ports if_cfg_wst* -filter "direction==out"]
set_output_delay -clock ${clock_name} [expr ${dc_clock_period}*0.4] [get_ports if_sram_cfg_est* -filter "direction==out"]
set_output_delay -clock ${clock_name} [expr ${dc_clock_period}*0.4] [get_ports if_sram_cfg_wst* -filter "direction==out"]
# cfg_clk_en is negative edge triggered
set_output_delay -clock ${clock_name} [expr ${dc_clock_period}*0.4] -clock_fall [get_ports *_clk_en -filter "direction==out"]


# set false path
# glb_tile_id is constant
set_false_path -from {glb_tile_id*}

# these inputs are from configuration register
set_false_path -from {cfg_tile_connected_wsti}
set_false_path -from {cfg_pc_tile_connected_wsti}
set_false_path -to {cfg_tile_connected_esto}
set_false_path -to {cfg_pc_tile_connected_esto}

# path from configuration registers are false path
set_false_path -through [get_cells glb_tile_int/glb_tile_cfg/glb_pio/pio_logic/*] -through [get_ports glb_tile_int/glb_tile_cfg/cfg_* -filter "direction==out"]
set_false_path -from [get_cells glb_tile_int/glb_tile_cfg/glb_pio/pio_logic/*] -through [get_ports glb_tile_int/glb_tile_cfg/cfg_* -filter "direction==out"]

# jtag cgra configuration read
# ignore timing when rd_en is 1
set_case_analysis 0 cgra_cfg_jtag_wsti_rd_en
set_multicycle_path -setup 10 -from cgra_cfg_jtag_wsti_rd_en
set_multicycle_path -hold 9 -from cgra_cfg_jtag_wsti_rd_en
set_multicycle_path -setup 10 -from cgra_cfg_jtag_wsti_addr -to cgra_cfg_jtag_esto_addr
set_multicycle_path -hold 9 -from cgra_cfg_jtag_wsti_addr -to cgra_cfg_jtag_esto_addr
set_multicycle_path -setup 10 -from cgra_cfg_jtag_wsti_data -to cgra_cfg_jtag_esto_data
set_multicycle_path -hold 9 -from cgra_cfg_jtag_wsti_data -to cgra_cfg_jtag_esto_data
set_false_path -from cgra_cfg_jtag_wsti_wr_en -to cgra_cfg_jtag_esto_wr_en

# jtag sram read
# jtag sram read is multicycle path because you assert rd_en for long cycles
set_multicycle_path -setup 10 -from [get_ports if_sram_cfg*rd* -filter "direction==in"]
set_multicycle_path -setup 10 -to [get_ports if_sram_cfg*rd* -filter "direction==out"]
set_multicycle_path -setup 10 -through [get_cells -hier if_sram_cfg*rd*]
set_multicycle_path -setup 10 -through [get_cells -hier cfg_sram_rd*]
set_multicycle_path -setup 10 -to [get_cells -hier if_sram_cfg*rd*]
set_multicycle_path -setup 10 -to [get_cells -hier cfg_sram_rd*]
set_multicycle_path -setup 10 -from [get_cells -hier if_sram_cfg*rd*]
set_multicycle_path -setup 10 -from [get_cells -hier cfg_sram_rd*]
set_multicycle_path -hold 9 -from [get_ports if_sram_cfg*rd* -filter "direction==in"]
set_multicycle_path -hold 9 -to [get_ports if_sram_cfg*rd* -filter "direction==out"]
set_multicycle_path -hold 9 -through [get_cells -hier if_sram_cfg*rd*]
set_multicycle_path -hold 9 -through [get_cells -hier cfg_sram_rd*]
set_multicycle_path -hold 9 -to [get_cells -hier if_sram_cfg*rd*]
set_multicycle_path -hold 9 -to [get_cells -hier cfg_sram_rd*]
set_multicycle_path -hold 9 -from [get_cells -hier if_sram_cfg*rd*]
set_multicycle_path -hold 9 -from [get_cells -hier cfg_sram_rd*]

# jtag write
# jtag sram write is asserted for 4 cycles from glc
set_multicycle_path -setup 4 -from [get_ports if_sram_cfg*wr* -filter "direction==in"]
set_multicycle_path -setup 4 -to [get_ports if_sram_cfg*wr* -filter "direction==out"]
set_multicycle_path -setup 4 -through [get_cells -hier if_sram_cfg*wr*]
set_multicycle_path -setup 4 -to [get_cells -hier if_sram_cfg*wr*]
set_multicycle_path -setup 4 -from [get_cells -hier if_sram_cfg*wr*]
set_multicycle_path -hold 3 -from [get_ports if_sram_cfg*wr* -filter "direction==in"]
set_multicycle_path -hold 3 -to [get_ports if_sram_cfg*wr* -filter "direction==out"]
set_multicycle_path -hold 3 -through [get_cells -hier if_sram_cfg*wr*]
set_multicycle_path -hold 3 -to [get_cells -hier if_sram_cfg*wr*]
set_multicycle_path -hold 3 -from [get_cells -hier if_sram_cfg*wr*]

# Make all signals limit their fanout
# loose fanout number to reduce the number of buffer and meet timing
set_max_fanout 20 $dc_design_name

# Make all signals meet good slew
# loose max_transition to reduce the number of buffer and meet timing
set_max_transition [expr 0.25*${dc_clock_period}] $dc_design_name

#set_input_transition 1 [all_inputs]
#set_max_transition 10 [all_outputs]

