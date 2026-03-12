#=========================================================================
# floorplan.tcl
#=========================================================================
# This script is called from the Innovus init flow step.

#-------------------------------------------------------------------------
# Floorplan variables
#-------------------------------------------------------------------------
 
set hori_pitch [dbGet top.fPlan.coreSite.size_x]
set vert_pitch [dbGet top.fPlan.coreSite.size_y]
set tech_pitch_x [expr 5 * $hori_pitch]
set tech_pitch_y [expr 1 * $vert_pitch]

set core_margin_left   $tech_pitch_x
set core_margin_bottom $tech_pitch_y
set core_margin_right  $tech_pitch_x
set core_margin_top    $tech_pitch_y

# try release some space horizontally
# (10*0.54) per mem, total 5.4*5 = 27um
set core_width  [expr 380 * $tech_pitch_x - $core_margin_left - $core_margin_right]
# set core_width  [expr 366 * $tech_pitch_x - $core_margin_left - $core_margin_right]
set core_height [expr 330 * $tech_pitch_y - $core_margin_top - $core_margin_bottom]

#-------------------------------------------------------------------------
# Floorplan
#-------------------------------------------------------------------------

floorPlan -s $core_width $core_height \
             $core_margin_left $core_margin_bottom $core_margin_right $core_margin_top

setFlipping s

#-------------------------------------------------------------------------
# SRAM Placement
#-------------------------------------------------------------------------
proc snap_to_grid {input granularity} {
   set new_value [expr ceil($input / $granularity) * $granularity]
   return $new_value
}

proc legalize_sram_x_location {x_loc} {
    global ADK_M3_TO_M8_STRIPE_OFSET_LIST
    set hori_pitch [dbGet top.fPlan.coreSite.size_x]
    set sram_x_granularity [lindex $ADK_M3_TO_M8_STRIPE_OFSET_LIST 2]
    set sram_x_granularity [snap_to_grid $sram_x_granularity $hori_pitch]
    set sram_x_granularity [expr 2 * $sram_x_granularity]
    return [snap_to_grid $x_loc $sram_x_granularity]
}

set srams [get_cells -quiet -hier -filter {is_memory_cell==true}]

# 1st SRAM
set sram_obj    [index_collection $srams 0]
set sram_name   [get_property $sram_obj full_name]
set sram_llx    [legalize_sram_x_location 39.00]
set sram_lly    [snap_to_grid 56.00 $tech_pitch_y]
set halo_left   $tech_pitch_x
set halo_bottom $tech_pitch_y
set halo_right  $tech_pitch_x
set halo_top    $tech_pitch_y
placeInstance $sram_name $sram_llx $sram_lly -fixed
addHaloToBlock $halo_left $halo_bottom $halo_right $halo_top -snapToSite $sram_name

# 2nd SRAM
set sram_obj    [index_collection $srams 1]
set sram_name   [get_property $sram_obj full_name]
set sram_llx    [legalize_sram_x_location 113.00]
set sram_lly    [snap_to_grid 56.00 $tech_pitch_y]
set halo_left   $tech_pitch_x
set halo_bottom $tech_pitch_y
set halo_right  $tech_pitch_x
set halo_top    $tech_pitch_y
placeInstance $sram_name $sram_llx $sram_lly -fixed
addHaloToBlock $halo_left $halo_bottom $halo_right $halo_top -snapToSite $sram_name
