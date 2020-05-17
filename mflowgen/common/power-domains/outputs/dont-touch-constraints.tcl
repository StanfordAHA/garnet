


#----------------------------------------------------------------
# Don't touch constraints 
#----------------------------------------------------------------

# Set dont_touch constraints on the clamping modules in SB/CBs
set_dont_touch [get_cells -hierarchical *u_mux_logic*]
set_dont_touch [get_nets -of_objects [get_ports *SB*]]
set_dont_touch [get_nets -of_objects [get_pins -of_objects [get_cells -hierarchical *u_mux_logic] -filter name=~*I*] -filter name=~*SB*]


# Set this so that the clamping modules in SB/CBs
# that have dont_touch attribute are uniquified
set init_design_uniquify 1

