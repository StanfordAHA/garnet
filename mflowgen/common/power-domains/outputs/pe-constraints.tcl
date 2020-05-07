

#=========================================================================
# Design Constraints File
#=========================================================================


# Constraints needed for power domains
# Load UPF file

set voltage_vdd 0.8
set voltage_gnd 0
set upf_create_implicit_supply_sets false
set_design_attributes -elements {.} -attribute enable_state_propagation_in_add_power_state TRUE
load_upf inputs/upf_Tile_PE.tcl 
