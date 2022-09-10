#=========================================================================
# globalnetconnect.tcl
#=========================================================================
# Author : 
# Date   : 

#-------------------------------------------------------------------------
# Global net connections for PG pins
#-------------------------------------------------------------------------

# Connect VNW / VPW if any cells have these pins

globalNetConnect VDD -type pgpin -pin VDD -inst *
globalNetConnect VDD -type tiehi
globalNetConnect VSS -type pgpin -pin VSS -inst *
globalNetConnect VSS -type tielo
globalNetConnect VSS -type pgpin -pin VPW -inst *
globalNetConnect VDD -type pgpin -pin VNW -inst *

