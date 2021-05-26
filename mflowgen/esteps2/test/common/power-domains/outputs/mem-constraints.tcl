


#=========================================================================
# Design Constraints File
#=========================================================================


# Constraints needed for power domains
# Load UPF file

# set voltage_vdd 0.8
# set voltage_gnd 0
# set upf_create_implicit_supply_sets false
# set_design_attributes -elements {.} -attribute enable_state_propagation_in_add_power_state TRUE
# load_upf inputs/upf_Tile_MemCore.tcl 

read_power_intent -1801 inputs/upf_Tile_MemCore.tcl -module Tile_MemCore
apply_power_intent -design Tile_MemCore -module Tile_MemCore
commit_power_intent -design Tile_MemCore
write_power_intent -1801 -design Tile_MemCore

# set_voltage ${voltage_vdd} -object_list {VDD VDD_SW}
# set_voltage ${voltage_gnd} -object_list {VSS}
# save_upf upf_${dc_design_name}.upf
