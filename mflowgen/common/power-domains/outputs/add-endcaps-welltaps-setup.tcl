
#-------------------------------------------------------------------------
# Endcap and well tap specification
#-------------------------------------------------------------------------



if { [info exists ::env(WHICH_SOC)] } {
    set WHICH_SOC $::env(WHICH_SOC)
} else {
    set WHICH_SOC "default"
}
deleteInst *TAP*
deleteInst *ENDCAP*
deleteInst *tap*

# Get M3 min width and signal routing pitch as defined in the LEF

set M3_min_width    [dbGet [dbGetLayerByZ 3].minWidth]
set M3_route_pitchX [dbGet [dbGetLayerByZ 3].pitchX]

# Set M3 stripe variables

set M3_str_width            [expr  3 * $M3_min_width]
set M3_str_pitch            [expr 20 * $M3_route_pitchX]

if { $WHICH_SOC == "amber" } {
  set M3_str_pitch          [expr 10 * $M3_route_pitchX]
}
set M3_str_intraset_spacing [expr ($M3_str_pitch - 2*$M3_str_width)/2]
set M3_str_interset_pitch   [expr 2*$M3_str_pitch]
set M3_str_offset           [expr $M3_str_pitch + $M3_route_pitchX/2 - $M3_str_width/2]

set core_llx [dbGet top.fPlan.coreBox_llx]

# Align tap cells with M3 pitch so that the M1 VPP pin is directly aligned with the M3 VDD net

# Pitch is a multiple of the M3 VDD stripe pitch 
set horiz_tap_pitch [expr $stripes_per_tap * $M3_str_interset_pitch]
set horiz_switch_pitch [expr $stripes_per_switch * $M3_str_interset_pitch]
