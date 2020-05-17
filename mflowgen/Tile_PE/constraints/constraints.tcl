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

# Set voltage groups
set_attribute [get_lib *90tt0p8v25c] default_threshold_voltage_group SVT
set_attribute [get_lib *lvt*] default_threshold_voltage_group LVT
set_attribute [get_lib *ulvt*] default_threshold_voltage_group ULVT

if $::env(PWR_AWARE) {
    source inputs/pe-constraints.tcl
} 

# Case analysis/scenarios

set alu_path PE_inst0/WrappedPE_inst0\$PE_inst0/ALU_inst0\$ALU_comb_inst0
set fp_add_path $alu_path/magma_BFloat_16_add_inst0
set fp_mul_path $alu_path/magma_BFloat_16_mul_inst0
set mul_path $alu_path/magma_Bits_32_mul_inst0
set add_path $alu_path/magma_Bits_17_add*

set lib_delay 0.03

########################################################################
# FP ADD
########################################################################
create_scenario fp_add

source inputs/common.tcl

set_case_analysis 0 [get_pins $alu_path/alu[7]]
set_case_analysis 0 [get_pins $alu_path/alu[6]]
set_case_analysis 0 [get_pins $alu_path/alu[5]]
set_case_analysis 1 [get_pins $alu_path/alu[4]]
set_case_analysis 0 [get_pins $alu_path/alu[3]]
set_case_analysis 1 [get_pins $alu_path/alu[2]]
set_case_analysis 1 [get_pins $alu_path/alu[1]]
set_case_analysis 0 [get_pins $alu_path/alu[0]]

# set false path for combinational path directly to i/o
set_false_path -from [all_inputs] -through [get_pins [list $fp_add_path/*]]
set_false_path -to [all_outputs] -through [get_pins [list $fp_add_path/*]]

set_false_path -through [get_pins [list $fp_mul_path/*]]
set_false_path -through [get_pins [list $mul_path/*]]
set_false_path -through [get_pins [list $add_path/*]]

set fp_add_min [expr 0.95+$lib_delay]
set fp_add_delay [expr $fp_add_min+0.17]
set_max_delay $fp_add_delay -through [get_pins [list $fp_add_path/*]]

########################################################################
# FP MUL
########################################################################
create_scenario fp_mul

source inputs/common.tcl

set_case_analysis 0 [get_pins $alu_path/alu[7]]
set_case_analysis 0 [get_pins $alu_path/alu[6]]
set_case_analysis 0 [get_pins $alu_path/alu[5]]
set_case_analysis 1 [get_pins $alu_path/alu[4]]
set_case_analysis 1 [get_pins $alu_path/alu[3]]
set_case_analysis 0 [get_pins $alu_path/alu[2]]
set_case_analysis 0 [get_pins $alu_path/alu[1]]
set_case_analysis 1 [get_pins $alu_path/alu[0]]

# set false path for combinational path directly to i/o
set_false_path -from [all_inputs] -through [get_pins [list $fp_mul_path/*]]
set_false_path -to [all_outputs] -through [get_pins [list $fp_mul_path/*]]

set_false_path -through [get_pins [list $fp_add_path/*]]
set_false_path -through [get_pins [list $mul_path/*]]
set_false_path -through [get_pins [list $add_path/*]]

set fp_mul_min [expr 0.75+$lib_delay]
set fp_mul_delay [expr $fp_mul_min+0.30]
set_max_delay $fp_mul_delay -through [get_pins [list $fp_mul_path/*]]

########################################################################
# MUL
########################################################################
create_scenario mul

source inputs/common.tcl

set_case_analysis 0 [get_pins $alu_path/alu[7]]
set_case_analysis 0 [get_pins $alu_path/alu[6]]
set_case_analysis 0 [get_pins $alu_path/alu[5]]
set_case_analysis 0 [get_pins $alu_path/alu[4]]
set_case_analysis 1 [get_pins $alu_path/alu[3]]
set_case_analysis 0 [get_pins $alu_path/alu[2]]
set_case_analysis 1 [get_pins $alu_path/alu[1]]
set_case_analysis 1 [get_pins $alu_path/alu[0]]

set_false_path -through [get_pins [list $fp_add_path/*]]
set_false_path -through [get_pins [list $fp_mul_path/*]]
set_false_path -through [get_pins [list $add_path/*]]

#set_false_path -through [get_pins [list $mul_path/*]] -to [get_pins [list $alu_path/*\$coreir_commonlib_mux2x16_inst0\$_join/*]]

set mul_min [expr 0.70+$i_delay+$o_delay]
set mul_delay [expr $mul_min+0.07]
set mul_delay 0.95
set_max_delay $mul_delay -through [get_pins [list $mul_path/*]]

########################################################################
# ADD
########################################################################
create_scenario add

source inputs/common.tcl

set_case_analysis 0 [get_pins $alu_path/alu[7]]
set_case_analysis 0 [get_pins $alu_path/alu[6]]
set_case_analysis 0 [get_pins $alu_path/alu[5]]
set_case_analysis 0 [get_pins $alu_path/alu[4]]
set_case_analysis 0 [get_pins $alu_path/alu[3]]
set_case_analysis 0 [get_pins $alu_path/alu[2]]
set_case_analysis 0 [get_pins $alu_path/alu[1]]
set_case_analysis 0 [get_pins $alu_path/alu[0]]

set_false_path -through [get_pins [list $fp_add_path/*]]
set_false_path -through [get_pins [list $fp_mul_path/*]]
set_false_path -through [get_pins [list $mul_path/*]]

set add_min [expr 0.65+$i_delay+$o_delay]
set add_delay [expr $add_min+0.02]
set add_delay 0.85
set_max_delay $add_delay -through [get_pins [list $add_path/*]]

########################################################################
# GENERAL
########################################################################
create_scenario default

source inputs/common.tcl

#set_false_path -through [get_pins [list $add_path/*]]
#set_false_path -through [get_pins [list $mul_path/*]]

set_false_path -from [all_inputs] -through [get_pins [list $fp_mul_path/*]]
set_false_path -to [all_outputs] -through [get_pins [list $fp_mul_path/*]]
set_false_path -from [all_inputs] -through [get_pins [list $fp_add_path/*]]
set_false_path -to [all_outputs] -through [get_pins [list $fp_add_path/*]]

# Constrain SB to ~200 ps
set sb_delay 0.210
# Use this first command to constrain all feedthrough paths to just the desired SB delay
set_max_delay -from SB*_IN_* -to SB*_OUT_* [expr ${sb_delay} + ${i_delay} + ${o_delay}]
# Then override the rest of the paths to be full clock period
set_max_delay -from SB*_IN_* -to SB*_OUT_* -through [get_pins [list CB*/* DECODE*/* PE_inst0*/* FEATURE*/*]] ${dc_clock_period}

########################################################################
source inputs/scenarios.tcl
set_active_scenarios $active_scenarios
########################################################################
