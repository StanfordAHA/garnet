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

# This script creates different timing constraints under different memory mode
# configurations.  The general flow is to define a scenario, read in a script
# containing generalized constraints for the designs, then provide overriding
# constraints in different operational modes.
set common_cnst inputs/common.tcl

# Set voltage groups
set_attribute [get_lib *90tt0p8v25c] default_threshold_voltage_group SVT
set_attribute [get_lib *lvt*] default_threshold_voltage_group LVT
set_attribute [get_lib *ulvt*] default_threshold_voltage_group ULVT

##############################
# Check for power aware
##############################
if $::env(PWR_AWARE) {
    source inputs/mem-constraints.tcl
}

##############################
# UNIFIED BUFFER MODE
##############################
create_scenario UNIFIED_BUFFER
set_operating_conditions tt0p8v25c -library tcbn16ffcllbwp16p90tt0p8v25c
set_tlu_plus_files -max_tluplus  $dc_tluplus_max \
                   -min_tluplus  $dc_tluplus_min \
                   -tech2itf_map $dc_tluplus_map

# Read common 
source -echo -verbose ${common_cnst}

# set_case_analysis ON MODE
set_case_analysis 0 MemCore_inst0/mode/Register*/O*[0]
set_case_analysis 0 MemCore_inst0/mode/Register*/O*[1]

### UNIFIED BUFFER CONSTRAINTS

###

##############################
# FIFO BUFFER MODE
##############################
create_scenario FIFO
set_operating_conditions tt0p8v25c -library tcbn16ffcllbwp16p90tt0p8v25c
set_tlu_plus_files -max_tluplus  $dc_tluplus_max \
                   -min_tluplus  $dc_tluplus_min \
                   -tech2itf_map $dc_tluplus_map

# Read common
source -echo -verbose ${common_cnst}

# set_case_analysis ON MODE
set_case_analysis 1 MemCore_inst0/mode/Register*/O*[0]
set_case_analysis 0 MemCore_inst0/mode/Register*/O*[1]

### FIFO CONSTRAINTS

###

##############################
# SRAM BUFFER MODE
##############################
create_scenario SRAM
set_operating_conditions tt0p8v25c -library tcbn16ffcllbwp16p90tt0p8v25c
set_tlu_plus_files -max_tluplus  $dc_tluplus_max \
                   -min_tluplus  $dc_tluplus_min \
                   -tech2itf_map $dc_tluplus_map

# Read common
source -echo -verbose ${common_cnst}

# set_case_analysis ON MODE
set_case_analysis 0 MemCore_inst0/mode/Register*/O*[0]
set_case_analysis 1 MemCore_inst0/mode/Register*/O*[1]

### SRAM CONSTRAINTS

###

#######################################################
# Set all scenarios for analysis
set_active_scenarios { UNIFIED_BUFFER FIFO SRAM }
#######################################################
