#=========================================================================
# Which SoC
#=========================================================================
if { [info exists ::env(WHICH_SOC)] } {
    set WHICH_SOC $::env(WHICH_SOC)
} else {
    set WHICH_SOC "onyx"
}

#=========================================================================
# General
#=========================================================================
# -- clock
set clock_net  clk
set clock_name ideal_clock
create_clock -name ${clock_name} \
             -period ${clock_period} \
             [get_ports ${clock_net}]

# -- load and drive
set_load -pin_load ${ADK_TYPICAL_ON_CHIP_LOAD} [all_outputs]
set_driving_cell -no_design_rule -lib_cell ${ADK_DRIVING_CELL} [all_inputs]

# -- fanout
set_max_fanout 10 ${design_name}

# -- transition
set_max_transition 50 ${design_name}

#=========================================================================
# Define Passthrough Signals
#=========================================================================
# -- Passthrough clock
set pt_clk_in [get_ports clk]
set pt_clk_out [get_ports clk*out*]

# -- Passthrough others
set pt_inputs [get_ports " \
    stall \
    config_config_data* \
    config_config_addr* \
    config_read* \
    config_write* \
    reset \
    flush"]
set pt_outputs [get_ports " \
    stall_out \
    config_out_config_data* \
    config_out_config_addr* \
    config_out_read* \
    config_out_write* \
    reset_out \
    flush_out"]

# -- Passthrough read_configread_config_data passthrough signals
#    More relaxed than the other passthrough signals
set pt_read_data_inputs [get_ports read_config_data_in]
set pt_read_data_outputs [get_ports read_config_data]

#=========================================================================
# Remove the driving cell from the passthrough signals
# (We are going to use an input/output slew and tighten a bit)
#=========================================================================
remove_driving_cell ${pt_clk_in}
remove_driving_cell ${pt_inputs}
remove_driving_cell ${pt_read_data_inputs}

#=========================================================================
# Input/Output Delay
#=========================================================================
# -- IO delay (Normal signals)
if { $WHICH_SOC == "amber" } {
    set i_delay [expr 0.2 * ${clock_period}]
} else {
    set i_delay [expr 0.3 * ${clock_period}]
}
set o_delay [expr 0.1 * ${clock_period}]

# -- IO delay (Passthrough signals)
# [input delay] Worst case of input delay
#               = max_diff(pt_clk, pt_data) * (Array Height-1)
#               This is a result after trail & error
# [output delay] For passthrough signals there is no point to add output delay
#                because we will constraint them using max/min delay
set pt_i_delay 700
set pt_o_delay 0

# -- Apply IO delay to general signals
set_input_delay  -clock ${clock_name} ${i_delay} [all_inputs -no_clocks]
set_output_delay -clock ${clock_name} ${o_delay} [all_outputs]

# -- Apply IO delay to passthrough signals
set_input_delay  -clock ${clock_name} ${pt_i_delay} ${pt_clk_in}
set_input_delay  -clock ${clock_name} ${pt_i_delay} ${pt_inputs}
set_input_delay  -clock ${clock_name} ${pt_i_delay} ${pt_read_data_inputs}
set_output_delay -clock ${clock_name} ${pt_o_delay} ${pt_clk_out}
set_output_delay -clock ${clock_name} ${pt_o_delay} ${pt_outputs}
set_output_delay -clock ${clock_name} ${pt_o_delay} ${pt_read_data_outputs}

#=========================================================================
# Max/Min Delay
#=========================================================================
# -- pt_clk
set min_delay_pt_clk [expr ${pt_i_delay} + ${pt_o_delay} + 0]
set max_delay_pt_clk [expr ${pt_i_delay} + ${pt_o_delay} + 30]
# set_min_delay -from ${pt_clk_in} -to ${pt_clk_out} ${min_delay_pt_clk}
# set_max_delay -from ${pt_clk_in} -to ${pt_clk_out} ${max_delay_pt_clk}
set_false_path -from ${pt_clk_in} -to ${pt_clk_out}

# -- pt_general
set min_delay_pt_general [expr ${max_delay_pt_clk} + 2]
set max_delay_pt_general [expr ${max_delay_pt_clk} + 30]
set_min_delay -to ${pt_outputs} ${min_delay_pt_general}
set_max_delay -to ${pt_outputs} ${max_delay_pt_general}

# -- pt_read_config
set min_delay_pt_rd_cfg [expr ${max_delay_pt_clk} + 10]
set max_delay_pt_rd_cfg [expr ${pt_i_delay} + ${pt_o_delay} + 300]
# read_config_data can come from (1) internal regs or (2) passthrough inputs
# For (1), the min delay is 50ps
# For (2), the min delay is 700+50=750ps (need to consider the input delay)
set_min_delay                              -to ${pt_read_data_outputs} 50
set_min_delay -from ${pt_read_data_inputs} -to ${pt_read_data_outputs} ${min_delay_pt_rd_cfg}
set_max_delay -from ${pt_read_data_inputs} -to ${pt_read_data_outputs} ${max_delay_pt_rd_cfg}

#=========================================================================
# Passthrough load capacitance
#=========================================================================
set mark_approx_cap 25
set_load ${mark_approx_cap} ${pt_outputs}
set_load ${mark_approx_cap} ${pt_read_data_outputs}
set_load ${mark_approx_cap} ${pt_clk_out}

#=========================================================================
# Signal Transition
#=========================================================================
set max_trans_passthru 20
set_max_transition ${max_trans_passthru} ${pt_outputs}
set_max_transition ${max_trans_passthru} ${pt_read_data_outputs}
# set_max_transition ${max_trans_passthru} ${pt_clk_out}

# Set input transition to match the max transition on outputs
set_input_transition ${max_trans_passthru} ${pt_clk_in}
set_input_transition ${max_trans_passthru} ${pt_inputs}
set_input_transition ${max_trans_passthru} ${pt_read_data_inputs}

#=========================================================================
# Multi-Cycle Path
#=========================================================================
# Relax config_addr -> read_config_data path
set_multicycle_path 2 -from [get_ports config_config_addr*] -to [get_ports read_config_data] -setup
set_multicycle_path 1 -from [get_ports config_config_addr*] -to [get_ports read_config_data] -hold
set_multicycle_path 2 -to [get_ports read_config_data* -filter direction==out] -setup
set_multicycle_path 1 -to [get_ports read_config_data* -filter direction==out] -hold

#=========================================================================
# Switch Box Delay
#=========================================================================
## Constrain SB to ~200 ps
set sb_delay 200
if { $WHICH_SOC == "amber" } {
    # Use this first command to constrain all feedthrough paths to just the desired SB delay
    set_max_delay -from SB*_IN_* -to SB*_OUT_* [expr ${sb_delay} + ${i_delay} + ${o_delay}]
    # Then override the rest of the paths to be full clock period
    set_max_delay -from SB*_IN_* -to SB*_OUT_* -through [get_pins [list CB*/* DECODE*/* MemCore_inst0*/* FEATURE*/*]] ${clock_period}
} else {
    # Use this first command to constrain all feedthrough paths to just the desired SB delay
    set_max_delay -from [get_ports SB* -filter direction==in] -to [get_ports SB* -filter direction==out] [expr ${sb_delay} + ${i_delay} + ${o_delay}]
    # Then override the rest of the paths to be full clock period
    set_max_delay -from [get_ports SB* -filter direction==in] -to [get_ports SB* -filter direction==out] -through [get_pins [list CB*/* DECODE*/* MemCore_inst0*/* FEATURE*/*]] ${clock_period}
}

########################################################################
# Misc.
########################################################################

if { $WHICH_SOC == "amber" } {
set_operating_conditions tt0p8v25c -library tcbn16ffcllbwp16p90tt0p8v25c
}

#=========================================================================
# False Path
#=========================================================================
# Tile ID
set_false_path -to [get_ports hi]
set_false_path -to [get_ports lo]
set_false_path -from [get_ports tile_id]

# Timing path to read_config_data output should never transition through a configuration
# register because we assume the register's value is constant during a read. 
set_false_path -through [get_cells -hier *config_reg_*] -to [get_ports read_config_data]

# False paths from config input ports to SB output ports
set_false_path -from [get_ports config* -filter direction==in] -to [get_ports SB* -filter direction==out]

# False paths from config input ports to SB registers
if { $WHICH_SOC == "amber" } {
    set sb_reg_path SB_ID0_5TRACKS_B*/REG_T*_B*/value__CE/value_reg*/*
    set_false_path -from [get_ports config_* -filter direction==in] -to [get_pins $sb_reg_path]
} else {
    set sb_reg_path SB_ID0_5TRACKS_B*_MemCore/REG_T*_B*/I
    set_false_path -from [get_ports config_* -filter direction==in] -through [get_pins $sb_reg_path]
}

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

#=========================================================================
# Dont Touch (for later constraints)
#=========================================================================
# Preserve the RMUXes so that we can easily constrain them later
set rmux_cells [get_cells -hier -regexp .*RMUX_.*_sel_(inst0|value)]
set_dont_touch $rmux_cells true
set_dont_touch [get_nets -of_objects [get_pins -of_objects $rmux_cells -filter name=~O*]] true
