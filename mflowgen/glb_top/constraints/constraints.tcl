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
             -period ${clock_period} \
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

###############################
# set_input_delay constraints for input ports
###############################

# set min delay for all inputs
set_min_delay -from [all_inputs] [expr ${clock_period}*0.45]
set_min_delay -from [get_ports proc_wr_data] [expr ${clock_period}*0.50]
set_min_delay -from [get_ports if_sram_cfg_rd_addr] [expr ${clock_period}*0.50]

# default input delay is 0.30
set_input_delay -clock ${clock_name} [expr ${clock_period}*0.30] [all_inputs]

# reset input delay is 0.2
set_input_delay -clock ${clock_name} [expr ${clock_period}*0.20] [get_ports reset]

# set input delay for cgra to glb 
set_input_delay -clock ${clock_name} [expr ${clock_period}*0.40] [get_ports stream_* -filter "direction==in"] -add_delay

# clk_en is not used
set_false_path -from [get_ports *_clk_en]

# cgra_cfg_jtag delay is 0.4 (from glc)
set_input_delay -clock ${clock_name} [expr ${clock_period}*0.40] [get_ports cgra_cfg_jtag*]

###############################
# set_output_delay constraints for output ports
###############################
# default output delay is 0.30
set_output_delay -clock ${clock_name} [expr ${clock_period}*0.30] [all_outputs]

# all output ports connected to cgra has high output delay
set_output_delay -clock ${clock_name} [expr ${clock_period}*0.4] [get_ports cgra_* -filter "direction==out"] -add_delay
set_output_delay -clock ${clock_name} [expr ${clock_period}*0.4] [get_ports stream_* -filter "direction==out"] -add_delay

###############################
# set_false path and multicycle path
###############################
# glc reading configuration registers is false path
set_false_path -from [get_ports cgra_cfg_jtag_gc2glb_rd_en]
# jtag bypass mode is false path
set_false_path -through [get_pins glb_tile_gen[*].glb_tile/*bypass]

# jtag sram read
set_multicycle_path -setup 10 -from [get_ports if_sram_cfg*rd* -filter "direction==in"]
set_multicycle_path -hold 9 -from [get_ports if_sram_cfg*rd* -filter "direction==in"]
set_multicycle_path -setup 10 -to [get_ports if_sram_cfg*rd* -filter "direction==out"]
set_multicycle_path -hold 9 -to [get_ports if_sram_cfg*rd* -filter "direction==out"]
set_multicycle_path -setup 10 -through [get_pins glb_tile_gen[*].glb_tile/if_sram*rd*]
set_multicycle_path -hold 9 -through [get_pins glb_tile_gen[*].glb_tile/if_sram*rd*]

# jtag write
set_multicycle_path -setup 4 -from [get_ports if_sram_cfg*wr* -filter "direction==in"]
set_multicycle_path -hold 3 -from [get_ports if_sram_cfg*wr* -filter "direction==in"]
set_multicycle_path -setup 4 -through [get_pins glb_tile_gen[*].glb_tile/if_sram*wr*]
set_multicycle_path -hold 3 -through [get_pins glb_tile_gen[*].glb_tile/if_sram*wr*]

# interrupt is asserted for 4 cycles 
set_multicycle_path -setup 4 -to [get_ports *interrupt_pulse -filter "direction==out"]
set_multicycle_path -hold 3 -to [get_ports *interrupt_pulse -filter "direction==out"]

# Make all signals limit their fanout

set_max_fanout 20 $design_name

# Make all signals meet good slew

set_max_transition [expr 0.10*${clock_period}] $design_name

#set_input_transition 1 [all_inputs]
#set_max_transition 10 [all_outputs]

set num_tiles [sizeof_collection [get_cells *glb_tile_gen*]]
for {set i 1} {$i < $num_tiles} {incr i} {
  # only need to set west since east pins are connected to same nets
  set nets [get_nets -of_objects [get_pins -of_objects [get_cells *glb_tile_gen[$i]*] -filter {name =~ *_wst*}]]
  query_objects $nets
  set_dont_touch $nets true
}

