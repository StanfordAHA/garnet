
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

addIoFiller -cell $ADK_IO_FILLER_CELLS_V  -logic -side top
addIoFiller -cell $ADK_IO_FILLER_CELLS_V  -logic -side bottom
addIoFiller -cell $ADK_IO_FILLER_CELLS_H  -logic -side left
addIoFiller -cell $ADK_IO_FILLER_CELLS_H  -logic -side right

snapFPlan -all
checkFPlan
