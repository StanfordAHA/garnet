
#-------------------------------------------------------------------------
# Endcap and well tap insertion 
#-------------------------------------------------------------------------

# Insert tap cells only on the boundary for SD domain if ADK specifies.
# Power switches will provide substrate connection for the core if no AON taps in adk.
# Insert both tap cells in the entire AON domain (since they dont have power switches)

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

if {[expr {$ADK_END_CAP_CELL == ""} && {$ADK_WELL_TAP_CELL == ""}]} {
    adk_add_endcap_well_taps_sd_pwr_domains
    adk_add_end_caps
    adk_add_endcap_well_taps_aon_pwr_domains  
}

# Only add taps in core area if ADK specifies an AON tap cell
if {[info exists ADK_AON_TAP_CELL] && [expr {$ADK_AON_TAP_CELL ne ""}]} {
   # NOT AMBER (amber adk.tcl does not set ADK_AON_TAP_CELL)
   set aon_tap_cell $ADK_AON_TAP_CELL
   set tap_width [dbGet [dbGetCellByName $aon_tap_cell].size_x]
   set tap_interval $horiz_tap_pitch
   # Set how many M3 stripe set intervals we want between switches and taps
   set num_stripe_intervals $vdd_m3_stripe_sparsity
   # Set how far from edge to start inserting tap columns
   # This location must align with M3 VDD stripe 
   set tap_edge_offset [expr $M3_str_offset + (2 * $M3_str_intraset_spacing + $M3_str_width) - ($tap_width / 4) + $tap_interval - ( $num_stripe_intervals * $M3_str_interset_pitch)]
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

