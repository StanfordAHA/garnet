#=========================================================================
# floorplan.tcl
#=========================================================================
# This script is called from the Innovus init flow step.

# Run this in floorplanning step to make io filler addition step happy
# (see add-io-fillers.tcl). Will be re-run in power step
delete_global_net_connections
# Standard cells
globalNetConnect VDD -type pgpin -pin vcc  -inst *
globalNetConnect VSS -type pgpin -pin vssx -inst *
# SRAMs
globalNetConnect VDD -type pgpin -pin vddp -inst *
globalNetConnect VSS -type pgpin -pin vss  -inst *
# IO Pads
globalNetConnect VDDPST -type pgpin -pin vccio -inst *
globalNetConnect VDD    -type pgpin -pin vcc   -inst *
globalNetConnect VSS    -type pgpin -pin vssp  -inst *
globalNetConnect VSS    -type pgpin -pin vssb  -inst *

set fp_width          3924.72
set fp_height         4084.92
set fp_margin_width   71.28
set fp_margin_height  71.82

floorPlan \
    -coreMarginsBy die \
    -d ${fp_width} ${fp_height} ${fp_margin_width} ${fp_margin_height} ${fp_margin_width} ${fp_margin_height}

# loadIoFile inputs/io_file -noAdjustDieSize
source inputs/io_pad_placement.tcl

# check_floorplan
checkFPlan
