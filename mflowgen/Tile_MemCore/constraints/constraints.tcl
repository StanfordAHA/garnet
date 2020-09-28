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

##############################
# Check for power aware
##############################
if $::env(PWR_AWARE) {
    source inputs/mem-constraints.tcl
}

create_mode -name UNIFIED_BUFFER
set_constraint_mode UNIFIED_BUFFER

# Read common 
source -echo -verbose ${common_cnst}

set_case_analysis 0 MemCore_inst0/LakeTop_W_inst0/mode[0]
set_case_analysis 0 MemCore_inst0/LakeTop_W_inst0/mode[1]

create_mode -name FIFO
set_constraint_mode FIFO

# Read common 
source -echo -verbose ${common_cnst}

set_case_analysis 1 MemCore_inst0/LakeTop_W_inst0/mode[0]
set_case_analysis 0 MemCore_inst0/LakeTop_W_inst0/mode[1]

create_mode -name SRAM
set_constraint_mode SRAM

# Read common 
source -echo -verbose ${common_cnst}

set_case_analysis 0 MemCore_inst0/LakeTop_W_inst0/mode[0]
set_case_analysis 1 MemCore_inst0/LakeTop_W_inst0/mode[1]
