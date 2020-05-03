

#-------------------------------------------------------------------------
# Endcap and well tap specification
#-------------------------------------------------------------------------


# TSMC16 requires specification of different taps/caps for different
# locations/orientations, which the foundation flow does not natively support

if {[expr {$ADK_END_CAP_CELL == ""} && {$ADK_WELL_TAP_CELL == ""}]} {
    
    deleteInst *TAP*
    deleteInst *ENDCAP*
    deleteInst *tap* 

    set flatten_effort $::env(flatten_effort) 
    set edge_offset    12.91

    addInst -cell BOUNDARY_PTAPBWP16P90_VPP_VSS -inst top_endcap_tap_1
    addInst -cell BOUNDARY_PTAPBWP16P90_VPP_VSS -inst top_endcap_tap_2
    
    placeInstance top_endcap_tap_1 -fixed [expr $edge_offset + 0*28      ] [expr [dbGet top.fplan.coreBox_ury] - $polypitch_y]
    placeInstance top_endcap_tap_2 -fixed [expr $edge_offset + 1*28 + 1.4] [expr [dbGet top.fplan.coreBox_ury] - $polypitch_y]
    
    addInst -cell BOUNDARY_PTAPBWP16P90_VPP_VSS -inst bot_endcap_tap_1
    addInst -cell BOUNDARY_PTAPBWP16P90_VPP_VSS -inst bot_endcap_tap_2
    
    placeInstance bot_endcap_tap_1 -fixed [expr $edge_offset + 0*28      ] $polypitch_y 
    placeInstance bot_endcap_tap_2 -fixed [expr $edge_offset + 1*28 + 1.4] $polypitch_y 

    if [expr $flatten_effort == 0] {
       addInst -cell BOUNDARY_PTAPBWP16P90_VPP_VSS -inst top_endcap_tap_3
       placeInstance top_endcap_tap_3 -fixed [expr $edge_offset + 2*28 + 1.4] [expr [dbGet top.fplan.coreBox_ury] - $polypitch_y]
       addInst -cell BOUNDARY_PTAPBWP16P90_VPP_VSS -inst bot_endcap_tap_3
       placeInstance bot_endcap_tap_3 -fixed [expr $edge_offset + 2*28 + 1.4] $polypitch_y
    }
} 

