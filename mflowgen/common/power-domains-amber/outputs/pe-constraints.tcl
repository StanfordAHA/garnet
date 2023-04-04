

#=========================================================================
# Design Constraints File
#=========================================================================


# Constraints needed for power domains
# Load UPF file

# set voltage_vdd 0.8
# set voltage_gnd 0
# set upf_create_implicit_supply_sets false
# set_design_attributes -elements {.} -attribute enable_state_propagation_in_add_power_state TRUE
# load_upf inputs/upf_Tile_PE.tcl 

read_power_intent -1801 inputs/upf_Tile_PE.tcl -module Tile_PE
apply_power_intent -design Tile_PE -module Tile_PE
commit_power_intent -design Tile_PE
write_power_intent -1801 -design Tile_PE
