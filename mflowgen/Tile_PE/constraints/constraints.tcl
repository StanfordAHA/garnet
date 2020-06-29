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

########################################################################
# GENERAL
########################################################################
create_scenario default

source inputs/common.tcl

set_false_path -from [all_inputs] -through [get_pins [list $fp_mul_path/*]]
set_false_path -to [all_outputs] -through [get_pins [list $fp_mul_path/*]]
set_false_path -from [all_inputs] -through [get_pins [list $fp_add_path/*]]
set_false_path -to [all_outputs] -through [get_pins [list $fp_add_path/*]]

########################################################################
# ALU OP SCENARIOS
########################################################################

exec python inputs/report_alu.py
source alu_op_scenarios.tcl

########################################################################
source inputs/scenarios.tcl
set_active_scenarios $active_scenarios
########################################################################
