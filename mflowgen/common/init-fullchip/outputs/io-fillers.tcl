
addIoFiller -cell $ADK_IO_FILLER_CELLS_V  -logic -side top
addIoFiller -cell $ADK_IO_FILLER_CELLS_V  -logic -side bottom
addIoFiller -cell $ADK_IO_FILLER_CELLS_H  -logic -side left
addIoFiller -cell $ADK_IO_FILLER_CELLS_H  -logic -side right

snapFPlan -all
checkFPlan
