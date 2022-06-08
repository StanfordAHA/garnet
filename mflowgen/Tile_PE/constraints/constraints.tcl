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

set alu_path PE_inst0/WrappedPE_inst0\$PE_inst0/ALU_inst0
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

##############################################################################
# steveri 01/2101 FIXME some of these set_false_path commands throw warnings e.g.
# Warning : At least one of the provided to-point is not a timing endpoint. [TIM-317]
#         : Provided to_point is '/designs/Tile_PE/instances_hier/PE_inst0/instances_hier/WrappedPE_inst0$PE_inst0/pins_in/inst[66]'.
# /designs/Tile_PE/modes/default_c/exceptions/path_disables/dis_3
##############################################################################

# Paths from config input ports to SB output ports
set_false_path -from [get_ports config* -filter direction==in] -to [get_ports SB* -filter direction==out]

# Paths from config input ports to SB data register inputs
set sb_reg_path SB_ID0_5TRACKS_B*_PE/REG_T*_B*/I
set_false_path -from [get_ports config_* -filter direction==in] -through [get_pins $sb_reg_path]
# Paths from config register outputs to SB data register inputs
set_false_path -through [get_cells -hier *config_reg_*] -through [get_pins $sb_reg_path]
# Paths from config register outputs to SB outputs
set_false_path -through [get_cells -hier *config_reg_*] -to [get_ports SB* -filter direction==out]

# Paths from config input ports to PE registers
set pe_path PE_inst0/WrappedPE_inst0\$PE_inst0
set_false_path -from [get_ports config_* -filter direction==in] -to [get_pins [list $pe_path/* ]]

# Paths from config input ports to the register file in Pond 
set pond_path PondCore_inst0/pond_W_inst0/pond/rf/data_array_reg*

# set_false_path -from [get_ports config_* -filter direction==in] -to [get_pins [list $pond_path/*]] -through [get_pins [list $pe_path/* ]]
# Set multicycle path from config ports to the register file passing through the ALU
# These are false paths and the above false path constraint can be applied but use MCP for conservative constraints
# The correct config paths from the config ports directly to the register file are verified to be constrained 
set_multicycle_path 2 -from [get_ports config_* -filter direction==in] -to [get_pins [list $pond_path/*]] -through [get_pins [list $pe_path/* ]] -setup
set_multicycle_path 1 -from [get_ports config_* -filter direction==in] -to [get_pins [list $pond_path/*]] -through [get_pins [list $pe_path/* ]] -hold

source -echo -verbose inputs/common.tcl

##############################################################################
# steveri 01/2101 Error b/c sometimes [get_pins] returns null...see fix below
# 
# set_false_path -from [all_inputs] -through [get_pins [list $fp_mul_path/*]]
# set_false_path -to [all_outputs] -through [get_pins [list $fp_mul_path/*]]
# set_false_path -from [all_inputs] -through [get_pins [list $fp_add_path/*]]
# set_false_path -to [all_outputs] -through [get_pins [list $fp_add_path/*]]
# 
##############################################################################

proc set_false_path_if_pins_exist { path } {
    set all_paths [list $path/*]; echo "all_paths=$all_paths"
    set pins [get_pins $all_paths]; echo "pins=$pins"
    if { $pins == "" } {
        echo "WARNING: No pins exist in path(s) $path"
        echo "WARNING: Cannot set false path"
    } {
        echo set_false_path -to [all_outputs] -through $pins
        set_false_path -to [all_outputs] -through $pins
        echo set_false_path -from [all_inputs] -through $pins
        set_false_path -from [all_inputs] -through $pins
    }
}
set_false_path_if_pins_exist $fp_mul_path
set_false_path_if_pins_exist $fp_add_path

########################################################################
# ALU OP SCENARIOS
########################################################################

# reports timing for each op
# but it slows down synthesis a lot, so disabling for now
#exec python inputs/report_alu.py
#source alu_op_scenarios.tcl

########################################################################
source inputs/scenarios.tcl
########################################################################
