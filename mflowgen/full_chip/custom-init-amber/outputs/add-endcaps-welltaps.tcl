#=========================================================================
# add-endcaps-welltaps.tcl
#=========================================================================
# Author : 
# Date   : 

#-------------------------------------------------------------------------
# Endcap and well tap specification
#-------------------------------------------------------------------------
# TSMC16 requires specification of different taps/caps for different
# locations/orientations, which the foundation flow does not natively support

if {[expr {$ADK_END_CAP_CELL == ""} && {$ADK_WELL_TAP_CELL == ""}]} {
  adk_set_end_cap_mode
  adk_set_well_tap_mode
  adk_add_end_caps
  adk_add_well_taps
}

