#=========================================================================
# floorplan.tcl
#=========================================================================
# This script is called from the Innovus init flow step to place all
# macros in the full chip floorplan
#
# Author : Alex Carsello
# Date   : March 19,2020

proc snap_to_grid {input granularity} {
   set new_value [expr ceil($input / $granularity) * $granularity]
   return $new_value
}

set hori_pitch [dbGet top.fPlan.coreSite.size_x]
set vert_pitch [dbGet top.fPlan.coreSite.size_y]
set tech_pitch_x [expr 5 * $hori_pitch]
set tech_pitch_y [expr 1 * $vert_pitch]

set place_tile_array 0
set place_glb_top 0
# set place_tile_array [expr !$::env(soc_only)]
# set place_glb_top [expr !$::env(soc_only)]

##############################################################################
###                        Placing Tile Array                              ###
##############################################################################
if { $place_tile_array } {
  # Params
  # Vertical distance (in # pitches) betwween GLB and Tile array
  set ic2glb_y_dist 330
  set glb2glc_y_dist 600
  set glb2srams_y_dist 1100

  ##############################################################################
  # Lots of congestion at top left corner of GLB, where the top
  # squeezes up against a row of alignment cells, so I'm moving the
  # GLB down a bit to open it up.
  # Tried moving down 15u, that wasn't enough, now increased to 45u.
  # (Note ic2glb_y_dist is in units of 'vert_pitches', and 45u ~ 78 vp's.)
  # FIXME later should express this as a function of alignment-cell location.
  set ic2glb_y_dist [expr $ic2glb_y_dist - 78]

  # power mesh vars
  set M3_route_pitchX [dbGet [dbGetLayerByZ 3].pitchX]    
  set M3_str_pitch [expr 10 * $M3_route_pitchX]

  # Horizonal stripes we need to align our blocks to
  set pmesh_bot_pitch [expr 20 * $M3_str_pitch]

  # Vertical stripes we need to align our blocks to
  set pmesh_top_pitch [expr 40 * $M3_str_pitch]
  
  # First, get the sizes of all Garnet macros (Interconnect,
  # global_buffer, and global_controller)
  
  set interconnect [get_cells -hier -filter {ref_lib_cell_name==Interconnect}]
  set interconnect_name [get_property $interconnect hierarchical_name]
  set ic_width [dbGet [dbGet -p top.insts.name $interconnect_name -i 0].cell.size_x]
  set ic_height [dbGet [dbGet -p top.insts.name $interconnect_name -i 0].cell.size_y]

  set ic_y_loc [snap_to_grid [expr ([dbGet top.fPlan.box_sizey] - $ic_height)/10.] $pmesh_bot_pitch]
  set ic_x_loc [snap_to_grid [expr ([dbGet top.fPlan.box_sizex] - $ic_width)/2.] $pmesh_top_pitch]
    
  placeinstance $interconnect_name $ic_x_loc $ic_y_loc -fixed
  addHaloToBlock [expr $hori_pitch * 15] $vert_pitch [expr $hori_pitch * 21] $vert_pitch $interconnect_name -snapToSite

  # Prevent power vias from blocking pins on interconnect (all pins on top edge)
  set ic_ury [expr $ic_y_loc + $ic_height]
  set ic_urx [expr $ic_x_loc + $ic_width]
  set thickness [expr 10 * $vert_pitch]
  createRouteBlk \
    -name ic_top_pg_via_blk \
    -cutLayer {4 5 6 7 8 9 10 11 12} \
    -pgnetonly \
    -box $ic_x_loc $ic_ury $ic_urx [expr $ic_ury + $thickness]

  # Prevent vias to PMESH_BOT_LAYER stripes over IC
  createRouteBlk \
    -name ic_pmesh_bot_via \
    -cutLayer [expr $ADK_POWER_MESH_BOT_LAYER + 1] \
    -pgnetonly \
    -box $ic_x_loc $ic_y_loc $ic_urx $ic_ury
  
  # Prevent PMESH_BOT_LAYER stripes over IC
  createRouteBlk \
    -name ic_pmesh_bot \
    -layer $ADK_POWER_MESH_BOT_LAYER \
    -pgnetonly \
    -box [expr $ic_x_loc + (8*$hori_pitch)] $ic_y_loc [expr $ic_urx - (8*$hori_pitch)] $ic_ury
  
  # Prevent PMESH_TOP_LAYER stripes over IC
  createRouteBlk \
    -name ic_pmesh_top \
    -layer $ADK_POWER_MESH_TOP_LAYER \
    -pgnetonly \
    -box $ic_x_loc [expr $ic_y_loc + (2*$vert_pitch)] $ic_urx [expr $ic_ury - (2*$vert_pitch)]
}

##############################################################################
###                        Placing GLB Top                                 ###
##############################################################################
if { $place_glb_top } {
  # GLB placement prep
  set glb [get_cells -hier -filter {ref_lib_cell_name==global_buffer}]
  set glb_name [get_property $glb hierarchical_name]
  set glb_width [dbGet [dbGet -p top.insts.name $glb_name -i 0].cell.size_x]
  set glb_height [dbGet [dbGet -p top.insts.name $glb_name -i 0].cell.size_y]

  set glb_y_loc [snap_to_grid [expr $ic_y_loc + $ic_height + ($vert_pitch * $ic2glb_y_dist)] $pmesh_bot_pitch]
  set glb_x_loc [snap_to_grid [expr ([dbGet top.fPlan.box_sizex] - $glb_width)/2.] $pmesh_top_pitch]
  
  # Place GLB
  placeinstance $glb_name $glb_x_loc $glb_y_loc -fixed
  addHaloToBlock [expr $hori_pitch * 15] $vert_pitch [expr $hori_pitch * 3] $vert_pitch $glb_name -snapToSite
  
  # Prevent power vias from blocking pins on GLB (pins on bottom and left edges)
  set glb_ury [expr $glb_y_loc + $glb_height]
  set glb_urx [expr $glb_x_loc + $glb_width]
  set thickness [expr 10 * $vert_pitch]
  createRouteBlk \
    -name glb_top_pg_via_blk \
    -cutLayer {4 5 6 7 8 9 10 11 12} \
    -pgnetonly \
    -box $glb_x_loc $glb_y_loc $glb_urx [expr $glb_y_loc - $thickness]
  
  createRouteBlk \
    -name glb_left_pg_via_blk \
    -cutLayer {4 5 6 7 8 9 10 11 12} \
    -pgnetonly \
    -box [expr $glb_x_loc - $thickness] $glb_y_loc $glb_x_loc $glb_ury
  
  # Prevent vias to PMESH_BOT_LAYER stripes over GLB
  createRouteBlk \
    -name glb_pmesh_bot_via \
    -cutLayer [expr $ADK_POWER_MESH_BOT_LAYER + 1]\
    -pgnetonly \
    -box $glb_x_loc $glb_y_loc $glb_urx $glb_ury
  
  # Prevent PMESH_BOT_LAYER stripes over GLB
  createRouteBlk \
    -name glb_pmesh_bot \
    -layer $ADK_POWER_MESH_BOT_LAYER \
    -pgnetonly \
    -box [expr $glb_x_loc + (8*$hori_pitch)] $glb_y_loc [expr $glb_urx - (8*$hori_pitch)] $glb_ury
  
  # Prevent PMESH_TOP_LAYER stripes over GLB
  createRouteBlk \
    -name glb_pmesh_top \
    -layer $ADK_POWER_MESH_TOP_LAYER \
    -pgnetonly \
    -box $glb_x_loc [expr $glb_y_loc + (2*$vert_pitch)] $glb_urx [expr $glb_ury - (2*$vert_pitch)]
}

##############################################################################
###                         Placing SoC SRAMs                              ###
##############################################################################
set srams [get_cells -hier -filter {is_memory_cell==true}]
set sram_name [get_property [index_collection $srams 0] hierarchical_name]
set sram_width [dbGet [dbGet -p top.insts.name $sram_name -i 0].cell.size_x]
set sram_height [dbGet [dbGet -p top.insts.name $sram_name -i 0].cell.size_y]
set num_of_srams 8
# TODO: should use dbGet to get this number:
set core_width 3780.432
set sram_gap [expr ($core_width - ($num_of_srams * $sram_width)) / ($num_of_srams + 1)]
set sram_loc_x [expr $sram_gap + 72.144]
set sram_loc_y [snap_to_grid 3701 $vert_pitch]

foreach_in_collection sram $srams {

  # get sram properties
  set sram_name [get_property $sram full_name]
  set sram_obj [dbGet -p top.insts.name $sram_name]
  set sram_llx [dbGet $sram_obj.box_llx]
  set sram_lly [dbGet $sram_obj.box_lly]
  set sram_urx [dbGet $sram_obj.box_urx]
  set sram_ury [dbGet $sram_obj.box_ury]

  # snap the sram to the grid, and place it
  set sram_x_loc_snap [snap_to_grid $sram_loc_x $hori_pitch]
  set sram_y_loc_snap [snap_to_grid $sram_loc_y $vert_pitch]
  # placeinstance $sram_name $sram_x_loc_snap $sram_y_loc_snap -fixed

  # add halo/routeblk to the sram
  set halo_left   $tech_pitch_x
  set halo_bottom $tech_pitch_y 
  set halo_right  $tech_pitch_x 
  set halo_top    [expr $tech_pitch_y + $vert_pitch]
  # addHaloToBlock $halo_left $halo_bottom $halo_right $halo_top -snapToSite $sram_name
  
  # add route block to the sram
  set sram_route_block_llx [snap_to_grid [expr $sram_llx - $halo_left]    $hori_pitch]
  set sram_route_block_lly [snap_to_grid [expr $sram_lly - $halo_bottom]  $vert_pitch]
  set sram_route_block_urx [snap_to_grid [expr $sram_urx + $halo_right]   $hori_pitch]
  set sram_route_block_ury [snap_to_grid [expr $sram_ury + $halo_top]     $vert_pitch]
  createRouteBlk -layer {m1 m2 m3 m4} -box "$sram_route_block_llx $sram_route_block_lly $sram_route_block_urx $sram_route_block_ury"

  # advance the sram location
  set sram_loc_x [expr $sram_loc_x + $sram_width + $sram_gap]

}

# Unplace any standard cells that got placed during init. Not sure why they're
# being placed, but they make power stripe generation take forever.
dbSet [dbGet top.insts.cell.baseClass core -p2].pStatus unplaced
