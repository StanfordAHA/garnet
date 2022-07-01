
#-------------------------------------------------------------------------
# Endcap and well tap specification
#-------------------------------------------------------------------------


# TSMC16 requires specification of different taps/caps for different
# locations/orientations, which the foundation flow doeps not natively support

if {[expr {$ADK_END_CAP_CELL == ""} && {$ADK_WELL_TAP_CELL == ""}]} {

    deleteInst *TAP*
    deleteInst *ENDCAP*
    deleteInst *tap*
    
    # Get M3 min width and signal routing pitch as defined in the LEF

    set M3_min_width    [dbGet [dbGetLayerByZ 3].minWidth]
    set M3_route_pitchX [dbGet [dbGetLayerByZ 3].pitchX]

    # Set M3 stripe variables

    set M3_str_width            [expr  3 * $M3_min_width]
    set M3_str_pitch            [expr 10 * $M3_route_pitchX]

    set M3_str_intraset_spacing [expr ($M3_str_pitch - 2*$M3_str_width)/2]
    set M3_str_interset_pitch   [expr 2*$M3_str_pitch]
    set M3_str_offset           [expr $M3_str_pitch + $M3_route_pitchX/2 - $M3_str_width/2]

    set core_llx [dbGet top.fPlan.coreBox_llx]
        
    # Align tap cells with M3 pitch so that the M1 VPP pin is directly aligned with the M3 VDD net
 
    # Pitch is a multiple of the M3 VDD stripe pitch 
    set horiz_tap_pitch [expr $stripes_per_tap * $M3_str_interset_pitch]
    set horiz_switch_pitch [expr $stripes_per_switch * $M3_str_interset_pitch]
    
    # Only add boundary taps if ADK specifies an AON boundary tap cell
    if {[info exists ADK_AON_BOUNDARY_TAP_CELL] && [expr {$ADK_AON_BOUNDARY_TAP_CELL ne ""}]} {
        set aon_tap_cell $ADK_AON_BOUNDARY_TAP_CELL
        set aon_tap_cell_width [dbGet [dbGetCellByName $aon_tap_cell].size_x]
 
        # Line up AON tap VDDC pin with M3 VDD stripe (3rd stripe in set of {VDD_SW VSS VDD}
        # We subtract (aon_tap_cell_with / 3) from offset to center of cell aligns with VDD, not edge of cell.
        # And cell's VDDC pin is slightly offset from center.
        set tap_edge_offset [expr $core_llx + $M3_str_offset + (2 * $M3_str_intraset_spacing + $M3_str_width) - ($aon_tap_cell_width / 3) + $horiz_tap_pitch]
 
        # Calculate how many tap cells can fit within width of block (-offset from left edge)
        set tap_cell_cnt [expr floor(([dbGet top.fPlan.coreBox_sizex] - ($tap_edge_offset)) / $horiz_tap_pitch) + 1]  

        set i 0
        while {$i < $tap_cell_cnt} {
           set cell_name_top endcap_tap_top_${i}
           addInst -cell $aon_tap_cell -inst $cell_name_top 
           # Find TAP cell that connects substrate to VDD, but power rail to VDD_SW
           placeInstance $cell_name_top -fixed [expr $tap_edge_offset + $i*$horiz_tap_pitch ] [expr [dbGet top.fplan.coreBox_ury] - $polypitch_y]
          
           set cell_name_bot endcap_tap_bot_${i}
           addInst -cell $aon_tap_cell -inst $cell_name_bot
           placeInstance $cell_name_bot -fixed [expr $tap_edge_offset + $i*$horiz_tap_pitch ]  $polypitch_y
 
           set i [expr $i + 1]
        }
    } else {
        echo "WARNING: Not adding boundary taps because ADK doesn't specify ADK_AON_BOUNDARY_TAP_CELL"
    }
    # Only add taps in core area if ADK specifies an AON tap cell
    if {[info exists ADK_AON_TAP_CELL] && [expr {$ADK_AON_TAP_CELL ne ""}]} {
       set aon_tap_cell $ADK_AON_TAP_CELL
       set tap_width [dbGet [dbGetCellByName $aon_tap_cell].size_x]
       # We really shouldn't have to add the polypitch here, but in practice
       # the pitch was off by 1 for some reason
       set tap_interval [expr $horiz_tap_pitch + $polypitch_x]
       # Start the taps 2 stripe set intervals to the left of the pwr switches
       set tap_edge_offset [expr $M3_str_offset + (2 * $M3_str_intraset_spacing + $M3_str_width) - ($tap_width / 3) + $horiz_switch_pitch - (2 * $M3_str_interset_pitch)]
       # Try adding well tap to SD domain
       addWellTap -cell $aon_tap_cell \
                  -prefix WELLTAP \
                  -cellInterval $tap_interval \
                  -inRowOffset $tap_edge_offset \
                  -fixedGap \
                  -powerDomain TOP
    } else {
       echo "WARNING: Not adding core area tap cells because ADK doesn't specity ADK_AON_TAP_CELL"
    }
}


