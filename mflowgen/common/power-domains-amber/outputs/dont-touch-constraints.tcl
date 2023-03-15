


#----------------------------------------------------------------
# Don't touch constraints 
#----------------------------------------------------------------


set_dont_touch [get_cells -hierarchical *u_mux_logic*] false
dbSet [dbGet top.insts.name *u_mux_logic* -p].dontTouch sizeOk

# Set dont_touch constraints on the clamping modules in SB/CBs
#foreach_in_collection cell  [get_cells -hier -filter "full_name=~*u_mux_logic* && ref_name=~AO22D0BWP16P90*"] {
#     set name [get_property $cell full_name]
#     dbSet [dbGetInstByName $name].useCells [list AO22D0BWP16P90 AO22D1BWP16P90 AO22D2BWP16P90 AO22D4BWP16P90]
# }

set_dont_touch [get_nets -of_objects [get_ports *SB*]]
set_dont_touch [get_nets -of_objects [get_pins -of_objects [get_cells -hierarchical *u_mux_logic] -filter name=~*I*] -filter name=~*SB*]


# Set this so that the clamping modules in SB/CBs
# that have dont_touch attribute are uniquified
set init_design_uniquify 1

