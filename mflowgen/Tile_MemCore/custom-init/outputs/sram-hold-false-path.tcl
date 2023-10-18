#=========================================================================
# sram-hold-false-path.tcl
#=========================================================================
# Some of the pins on SRAM have gigantic hold time requirements.
# However, the inputs to those pins are either static or only toggle
# during reset. This means that we can safely ignore the hold time
# Author : 
# Date   : 

set_false_path -hold -to [get_pins -hierarchical *fwen]
set_false_path -hold -to [get_pins -hierarchical *clkbyp]
set_false_path -hold -to [get_pins -hierarchical *mcen]
set_false_path -hold -to [get_pins -hierarchical *mc]
set_false_path -hold -to [get_pins -hierarchical *wpulseen]
set_false_path -hold -to [get_pins -hierarchical *wpulse]
set_false_path -hold -to [get_pins -hierarchical *wa]
