#=========================================================================
# globalnetconnect.tcl
#=========================================================================
# Author : 
# Date   : 

#-------------------------------------------------------------------------
# Global net connections for PG pins
#-------------------------------------------------------------------------

set WHICH_SOC "onyx"
if { [info exists ::env(WHICH_SOC)] } { set WHICH_SOC $::env(WHICH_SOC) }

# Connect VNW / VPW if any cells have these pins

globalNetConnect VDD -type pgpin -pin VDD -inst *
globalNetConnect VDD -type tiehi
globalNetConnect VSS -type pgpin -pin VSS -inst *
globalNetConnect VSS -type tielo

if { $WHICH_SOC == "amber" } {
    globalNetConnect VDD -type pgpin -pin VPP -inst *
    globalNetConnect VSS -type pgpin -pin VBB -inst *
} else {
    globalNetConnect VSS -type pgpin -pin VPW -inst *
    globalNetConnect VDD -type pgpin -pin VNW -inst *
}
