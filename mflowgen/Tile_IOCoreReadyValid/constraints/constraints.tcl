#=========================================================================
# Design Constraints File
#=========================================================================

set_units -time ps -capacitance fF


########################################################################
# GENERAL
########################################################################
create_mode -name default_c
set_constraint_mode default_c

# Paths from config input ports to SB output ports
set_false_path -from [get_ports config* -filter direction==in] -to [get_ports SB* -filter direction==out]

# Paths from config input ports to SB data register inputs
# set sb_reg_path SB_ID*_*TRACKS_B*_IOCoreReadyValid/REG_T*_B*/I
set sb_reg_path {SB_ID[0-9]+_[0-9]+TRACKS_B[0-9]+_IOCoreReadyValid/REG_T[0-9]+_.*_B[0-9]+/I.*}
set_false_path -from [get_ports config_* -filter direction==in] -through [get_pins -regexp $sb_reg_path]
# Paths from config register outputs to SB data register inputs
set_false_path -through [get_cells -hier *config_reg_*] -through [get_pins -regexp $sb_reg_path]
# Paths from config register outputs to SB outputs
set_false_path -through [get_cells -hier *config_reg_*] -to [get_ports SB* -filter direction==out]

# Paths from config input ports to PE registers
# set core_path PE_inst0/PE_inner_W_inst0/PE_inner
set core_path IOCoreReadyValid_inst0/io_core_64_W_inst0/io_core_64
set_false_path -from [get_ports config_* -filter direction==in] -through [get_pins [list $core_path/* ]]

source -echo -verbose inputs/common.tcl

########################################################################
source inputs/scenarios.tcl
########################################################################
