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

# set_input_delay constraints for input ports
#
# - make this non-zero to avoid hold buffers on input-registered designs

set_input_delay  -clock ${clock_name} [expr ${dc_clock_period}*0.8] [ all_inputs ]
set_output_delay -clock ${clock_name} [expr ${dc_clock_period}*0.8] [ list read_config_data ]
#set_input_delay  -clock ${clock_name} [expr ${dc_clock_period}*0.2] [ list chain_data_in chain_valid_in config_addr_in config_data_in config_en config_read config_write flush ren_in wen_in ]
set_output_delay -clock ${clock_name} [expr ${dc_clock_period}*0.2] [ list hi lo config_out_write config_out_read config_out_config_data config_out_config_addr SB_T2_WEST_SB_OUT_B16 SB_T2_WEST_SB_OUT_B1 SB_T2_SOUTH_SB_OUT_B16 SB_T2_SOUTH_SB_OUT_B1 SB_T2_NORTH_SB_OUT_B16 SB_T2_NORTH_SB_OUT_B1 SB_T2_EAST_SB_OUT_B16 SB_T2_EAST_SB_OUT_B1 SB_T1_WEST_SB_OUT_B16 SB_T1_WEST_SB_OUT_B1 SB_T1_SOUTH_SB_OUT_B16 SB_T1_SOUTH_SB_OUT_B1 SB_T1_NORTH_SB_OUT_B16 SB_T1_NORTH_SB_OUT_B1 SB_T1_EAST_SB_OUT_B16 SB_T1_EAST_SB_OUT_B1 SB_T0_WEST_SB_OUT_B16 SB_T0_WEST_SB_OUT_B1 SB_T0_SOUTH_SB_OUT_B16 SB_T0_SOUTH_SB_OUT_B1 SB_T0_NORTH_SB_OUT_B16 SB_T0_NORTH_SB_OUT_B1 SB_T0_EAST_SB_OUT_B16 SB_T0_EAST_SB_OUT_B1]

# set_output_delay constraints for output ports


# Make all signals limit their fanout

set_max_fanout 20 $dc_design_name

# Make all signals meet good slew

set_max_transition [expr 0.25*${dc_clock_period}] $dc_design_name

#set_input_transition 1 [all_inputs]
#set_max_transition 10 [all_outputs]

