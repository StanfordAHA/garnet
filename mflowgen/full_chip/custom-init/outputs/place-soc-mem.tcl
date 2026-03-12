#=========================================================================
# place-soc-mem.tcl
#=========================================================================
#
# Author : Po-Han Chen
# Date   : 

proc snap_to_grid {input granularity} {
   set new_value [expr ceil($input / $granularity) * $granularity]
   return $new_value
}

proc legalize_sram_x_location {x_loc} {
    global ADK_M3_TO_M8_STRIPE_OFSET_LIST
    set hori_pitch [dbGet top.fPlan.coreSite.size_x]
    set vert_pitch [dbGet top.fPlan.coreSite.size_y]
    set tech_pitch_x [expr 5 * $hori_pitch]
    set tech_pitch_y [expr 1 * $vert_pitch]
    set sram_x_granularity [lindex $ADK_M3_TO_M8_STRIPE_OFSET_LIST 2]
    set sram_x_granularity [snap_to_grid $sram_x_granularity $hori_pitch]
    set sram_x_granularity [expr 2 * $sram_x_granularity]
    return [snap_to_grid $x_loc $sram_x_granularity]
}

set hori_pitch [dbGet top.fPlan.coreSite.size_x]
set vert_pitch [dbGet top.fPlan.coreSite.size_y]
set tech_pitch_x [expr 5 * $hori_pitch]
set tech_pitch_y [expr 1 * $vert_pitch]

#-------------------------------------------------------------------------
# Collect Tile Information
#-------------------------------------------------------------------------
set srams [get_cells -hier -filter {is_memory_cell==true}]
set sram_name [get_property [index_collection $srams 0] hierarchical_name]
set sram_width [dbGet [dbGet -p top.insts.name $sram_name -i 0].cell.size_x]
set sram_height [dbGet [dbGet -p top.insts.name $sram_name -i 0].cell.size_y]
set num_of_srams 8
set core_width [dbGet top.fPlan.coreBox_sizex]
set sram_gap [expr ($core_width - ($num_of_srams * $sram_width)) / ($num_of_srams + 1)]
# set sram_loc_x [expr $sram_gap + [dbGet top.fPlan.coreBox_llx]]
set sram_loc_x [snap_to_grid 102.06 $tech_pitch_x]
set sram_loc_y [expr [dbGet top.fPlan.coreBox_ury] - 14.12 - $sram_height]

# snap to grid
set sram_loc_x [snap_to_grid $sram_loc_x $hori_pitch]
set sram_loc_y [snap_to_grid $sram_loc_y $vert_pitch]

set i 0
foreach_in_collection sram $srams {

  # get sram properties
  set sram_name [get_property $sram full_name]
  set sram_obj [dbGet -p top.insts.name $sram_name]
  
  # snap the sram to the grid, and place it
  placeinstance \
      $sram_name \
      [legalize_sram_x_location $sram_loc_x] \
      $sram_loc_y \
      -fixed

  # add halo/routeblk to the sram
  set halo_left   $tech_pitch_x
  set halo_bottom $tech_pitch_y
  set halo_right  $tech_pitch_x
  set halo_top    $tech_pitch_y
  addHaloToBlock $halo_left $halo_bottom $halo_right $halo_top -snapToSite $sram_name
  
  # add route block to the sram
  set sram_llx [dbGet $sram_obj.box_llx]
  set sram_lly [dbGet $sram_obj.box_lly]
  set sram_urx [dbGet $sram_obj.box_urx]
  set sram_ury [dbGet $sram_obj.box_ury]
  set sram_route_block_llx [snap_to_grid [expr $sram_llx - $halo_left]    $hori_pitch]
  set sram_route_block_lly [snap_to_grid [expr $sram_lly - $halo_bottom]  $vert_pitch]
  set sram_route_block_urx [snap_to_grid [expr $sram_urx + $halo_right]   $hori_pitch]
  set sram_route_block_ury [snap_to_grid [expr $sram_ury + $halo_top]     $vert_pitch]
  # for some unknown reason, this route block will be moved to the origin and block others...
  # disable it for now, investigate later
  # createRouteBlk -layer {m1 m2 m3 m4} -box "$sram_route_block_llx $sram_route_block_lly $sram_route_block_urx $sram_route_block_ury"
  echo "$sram_route_block_llx $sram_route_block_lly $sram_route_block_urx $sram_route_block_ury"

  # advance the sram location
  # set sram_loc_x [expr $sram_loc_x + $sram_width + $sram_gap]
  set sram_loc_x [expr $sram_loc_x + $sram_width]
  if {$i == 3} {
    set sram_loc_x [snap_to_grid 2849.9 $tech_pitch_x]
  }
  incr i
}

# Unplace any standard cells that got placed during init. Not sure why they're
# being placed, but they make power stripe generation take forever.
dbSet [dbGet top.insts.cell.baseClass core -p2].pStatus unplaced
