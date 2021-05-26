
#-------------------------------------------------------------------------
# Endcap and well tap specification
#-------------------------------------------------------------------------


# TSMC16 requires specification of different taps/caps for different
# locations/orientations, which the foundation flow doeps not natively support

if {[expr {$ADK_END_CAP_CELL == ""} && {$ADK_WELL_TAP_CELL == ""}]} {

    deleteInst *TAP*
    deleteInst *ENDCAP*
    deleteInst *tap*

    # Align tap cells with M3 pitch so that the M1 VPP pin is directly aligned with the M3 VDD net

    # Get M3 min width and signal routing pitch as defined in the LEF

    set M3_min_width    [dbGet [dbGetLayerByZ 3].minWidth]
    set M3_route_pitchX [dbGet [dbGetLayerByZ 3].pitchX]

    # Set M3 stripe variables

    set M3_str_width            [expr  3 * $M3_min_width]
    set M3_str_pitch            [expr 10 * $M3_route_pitchX]

    set M3_str_intraset_spacing [expr ($M3_str_pitch - 2*$M3_str_width)/2]
    set M3_str_interset_pitch   [expr 2*$M3_str_pitch]
    set M3_str_offset           [expr $M3_str_pitch + $M3_route_pitchX/2 - $M3_str_width/2]
    
    # Aligned with M3 power straps
    # If ordering of the power straps change, the multiplication factor needs to change 
    set edge_offset [expr $M3_str_offset + ($M3_str_intraset_spacing + $M3_str_width)*48]

    # Same pitch as power pitches 
    set horiz_pitch [expr 420 * $polypitch_x]

    # Left offset
    # Same left offset as power switches
    set left_offset 16
   
    set tap_cell_cnt [expr floor(([dbGet top.fPlan.coreBox_urx] - $left_offset - 3) / $horiz_pitch) + 1]  

    # Calculated from horiz_pitch 
    set pitch_offset 27
    
    set i 0
    while {$i < $tap_cell_cnt} {
       set cell_name_top endcap_tap_top_${i}
       addInst -cell BOUNDARY_PTAPBWP16P90_VPP_VSS -inst $cell_name_top 
       placeInstance $cell_name_top -fixed [expr $edge_offset + $i*$pitch_offset*$M3_str_interset_pitch ] [expr [dbGet top.fplan.coreBox_ury] - $polypitch_y]
      
       set cell_name_bot endcap_tap_bot_${i}
       addInst -cell BOUNDARY_PTAPBWP16P90_VPP_VSS -inst $cell_name_bot
       placeInstance $cell_name_bot -fixed [expr $edge_offset + $i*$pitch_offset*$M3_str_interset_pitch ]  $polypitch_y
 
       set i [expr $i + 1]
     }

}


