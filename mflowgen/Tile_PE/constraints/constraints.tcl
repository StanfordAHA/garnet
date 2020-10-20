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
# set_attribute [get_lib *90tt0p8v25c] default_threshold_voltage_group SVT
# set_attribute [get_lib *lvt*] default_threshold_voltage_group LVT
# set_attribute [get_lib *ulvt*] default_threshold_voltage_group ULVT

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
create_mode -name default_c
set_constraint_mode default_c


# Constraints for false paths that show up when PondCore is introduced
# Constraints are also valid for baseline PE, but these false paths are
# not a concern for timing for the baseline PE

# Paths from config input ports to SB output ports
set_false_path -from [get_ports config* -filter direction==in] -to [get_ports SB* -filter direction==out]

# Paths from config input ports to SB registers
set sb_reg_path SB_ID0_5TRACKS_B*_PE/REG_T*_B*/value__CE/value_reg[*]/*
set_false_path -from [get_ports config_* -filter direction==in] -to [get_pins $sb_reg_path]

# Paths from config input ports to PE registers
set pe_path PE_inst0/WrappedPE_inst0\$PE_inst0
set_false_path -from [get_ports config_* -filter direction==in] -to [get_pins [list $pe_path/* ]]

source -echo -verbose inputs/common.tcl

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
########################################################################
