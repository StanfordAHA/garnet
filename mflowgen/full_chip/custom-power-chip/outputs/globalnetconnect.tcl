#=========================================================================
# globalnetconnect.tcl
#=========================================================================
# Author : 
# Date   : 

#-------------------------------------------------------------------------
# Global net connections for PG pins
#-------------------------------------------------------------------------

globalNetConnect VDD -type pgpin -pin VDD -inst *
globalNetConnect VDD -type tiehi
globalNetConnect VSS -type pgpin -pin VSS -inst *
globalNetConnect VSS -type tielo
# stdcells
globalNetConnect VDD -type pgpin -pin vcc    -inst *
globalNetConnect VSS -type pgpin -pin vssx   -inst *
# SRAMs
globalNetConnect VDD -type pgpin -pin vddp    -inst *
globalNetConnect VSS -type pgpin -pin vss     -inst *
