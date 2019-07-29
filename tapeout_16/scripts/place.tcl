source ../../scripts/tool_settings.tcl
#Constraints
set_interactive_constraint_modes [all_constraint_modes]
set_dont_touch true [get_nets -of */PAD]
set_interactive_constraint_mode {}

### Place Design
place_opt_design -place

saveDesign init_place.enc -def -tcon -verilog

place_opt_design -opt

setTieHiLoMode -maxDistance 20 -maxFanout 16
addTieHiLo -cell "TIEHBWP16P90 TIELBWP16P90"
