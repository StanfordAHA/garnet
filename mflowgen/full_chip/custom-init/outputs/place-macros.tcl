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

# set place_tile_array [expr !$::env(soc_only)]
# set place_glb_top [expr !$::env(soc_only)]
set place_tile_array 1
set place_glb_top 1
set place_diff_clk_rcvr 0

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

  # set ic_x_loc [snap_to_grid [expr ([dbGet top.fPlan.box_sizex] - $ic_width)/2.] $pmesh_top_pitch]
  # set ic_y_loc [snap_to_grid [expr ([dbGet top.fPlan.box_sizey] - $ic_height)/10.] $pmesh_bot_pitch]
  set ic_x_loc [snap_to_grid 96.984 $tech_pitch_x] 
  set ic_y_loc [snap_to_grid 89.46 $tech_pitch_y] 
  
  placeinstance $interconnect_name $ic_x_loc $ic_y_loc -fixed
  # addHaloToBlock [expr $hori_pitch * 15] $vert_pitch [expr $hori_pitch * 21] $vert_pitch $interconnect_name -snapToSite
  addHaloToBlock \
      [expr $tech_pitch_x * 1] \
      [expr $tech_pitch_y * 2] \
      [expr $tech_pitch_x * 1] \
      [expr $tech_pitch_y * 2] \
      $interconnect_name \
      -snapToSite

  # top/bottom routing blockage (signal: all except m5)
  set ic_rblk_left   [expr $tech_pitch_x * 0.5 - 0.1]
  set ic_rblk_right  [expr $tech_pitch_x * 0.5 - 0.1]
  set ic_rblk_top    [expr $tech_pitch_y * 1]
  set ic_rblk_bottom [expr $tech_pitch_y * 1]
  set ic_rblk_llx [expr $ic_x_loc]
  set ic_rblk_lly [expr $ic_y_loc - $ic_rblk_bottom]
  set ic_rblk_urx [expr $ic_x_loc + $ic_width]
  set ic_rblk_ury [expr $ic_y_loc + $ic_height + $ic_rblk_top]
  createRouteBlk \
      -name ic_route_block_top_bottom_sig \
      -layer {m1 m2 m3 m4 m6 m7 m8}  \
      -box "$ic_rblk_llx $ic_rblk_lly $ic_rblk_urx $ic_rblk_ury" \
      -exceptpgnet
  
  # top/bottom routing blockage (power, all)
  set ic_rblk_left   [expr $tech_pitch_x * 1 - 0.04]
  set ic_rblk_right  [expr $tech_pitch_x * 1 - 0.04]
  set ic_rblk_top    [expr $tech_pitch_y * 2 - 0.08]
  set ic_rblk_bottom [expr $tech_pitch_y * 2 - 0.08]
  set ic_rblk_llx [expr $ic_x_loc]
  set ic_rblk_lly [expr $ic_y_loc - $ic_rblk_bottom]
  set ic_rblk_urx [expr $ic_x_loc + $ic_width]
  set ic_rblk_ury [expr $ic_y_loc + $ic_height + $ic_rblk_top]
  createRouteBlk \
      -name ic_route_block_top_bottom_pwr \
      -layer {m1 m2 m3 m4 m5 m6 m7 m8}  \
      -box "$ic_rblk_llx $ic_rblk_lly $ic_rblk_urx $ic_rblk_ury" \
      -pgnetonly
  
  # left/right routing blockage (signal: all except m6)
  set ic_rblk_left   [expr $tech_pitch_x * 0.5 - 0.1]
  set ic_rblk_right  [expr $tech_pitch_x * 0.5 - 0.1]
  set ic_rblk_top    [expr $tech_pitch_y * 1]
  set ic_rblk_bottom [expr $tech_pitch_y * 1]
  set ic_rblk_llx [expr $ic_x_loc - $ic_rblk_left]
  set ic_rblk_lly [expr $ic_y_loc]
  set ic_rblk_urx [expr $ic_x_loc + $ic_width + $ic_rblk_right]
  set ic_rblk_ury [expr $ic_y_loc + $ic_height]
  createRouteBlk \
      -name ic_route_block_left_right_sig \
      -layer {m1 m2 m3 m4 m5 m7 m8}  \
      -box "$ic_rblk_llx $ic_rblk_lly $ic_rblk_urx $ic_rblk_ury" \
      -exceptpgnet
  
  # left/right routing blockage (power, all)
  set ic_rblk_left   [expr $tech_pitch_x * 1 - 0.04]
  set ic_rblk_right  [expr $tech_pitch_x * 1 - 0.04]
  set ic_rblk_top    [expr $tech_pitch_y * 2 - 0.08]
  set ic_rblk_bottom [expr $tech_pitch_y * 2 - 0.08]
  set ic_rblk_llx [expr $ic_x_loc - $ic_rblk_left]
  set ic_rblk_lly [expr $ic_y_loc]
  set ic_rblk_urx [expr $ic_x_loc + $ic_width + $ic_rblk_right]
  set ic_rblk_ury [expr $ic_y_loc + $ic_height]
  createRouteBlk \
      -name ic_route_block_left_right_pwr \
      -layer {m1 m2 m3 m4 m5 m6 m7 m8}  \
      -box "$ic_rblk_llx $ic_rblk_lly $ic_rblk_urx $ic_rblk_ury" \
      -pgnetonly

  # # Prevent power vias from blocking pins on interconnect (all pins on top edge)
  # set ic_ury [expr $ic_y_loc + $ic_height]
  # set ic_urx [expr $ic_x_loc + $ic_width]
  # set thickness [expr 10 * $vert_pitch]
  # createRouteBlk \
  #   -name ic_top_pg_via_blk \
  #   -cutLayer {4 5 6 7 8 9 10 11 12} \
  #   -pgnetonly \
  #   -box $ic_x_loc $ic_ury $ic_urx [expr $ic_ury + $thickness]

  # # Prevent vias to PMESH_BOT_LAYER stripes over IC
  # createRouteBlk \
  #   -name ic_pmesh_bot_via \
  #   -cutLayer [expr $ADK_POWER_MESH_BOT_LAYER + 1] \
  #   -pgnetonly \
  #   -box $ic_x_loc $ic_y_loc $ic_urx $ic_ury
  
  # # Prevent PMESH_BOT_LAYER stripes over IC
  # createRouteBlk \
  #   -name ic_pmesh_bot \
  #   -layer $ADK_POWER_MESH_BOT_LAYER \
  #   -pgnetonly \
  #   -box [expr $ic_x_loc + (8*$hori_pitch)] $ic_y_loc [expr $ic_urx - (8*$hori_pitch)] $ic_ury
  
  # # Prevent PMESH_TOP_LAYER stripes over IC
  # createRouteBlk \
  #   -name ic_pmesh_top \
  #   -layer $ADK_POWER_MESH_TOP_LAYER \
  #   -pgnetonly \
  #   -box $ic_x_loc [expr $ic_y_loc + (2*$vert_pitch)] $ic_urx [expr $ic_ury - (2*$vert_pitch)]
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

  # set glb_x_loc [snap_to_grid [expr ([dbGet top.fPlan.box_sizex] - $glb_width)/2.] $pmesh_top_pitch]
  # set glb_y_loc [snap_to_grid [expr $ic_y_loc + $ic_height + ($vert_pitch * $ic2glb_y_dist)] $pmesh_bot_pitch]
  set glb_x_loc [snap_to_grid 100.224 $tech_pitch_x]
  set glb_y_loc [snap_to_grid 3133.62 $tech_pitch_y]

  # Place GLB
  placeinstance $glb_name $glb_x_loc $glb_y_loc -fixed
  # addHaloToBlock [expr $hori_pitch * 15] $vert_pitch [expr $hori_pitch * 3] $vert_pitch $glb_name -snapToSite
  addHaloToBlock \
      [expr $tech_pitch_x * 1] \
      [expr $tech_pitch_y * 2] \
      [expr $tech_pitch_x * 1] \
      [expr $tech_pitch_y * 2] \
      $glb_name \
      -snapToSite
  
  # top/bottom routing blockage (signal: all except m5, m7)
  set glb_rblk_left   [expr $tech_pitch_x * 0.5 - 0.1]
  set glb_rblk_right  [expr $tech_pitch_x * 0.5 - 0.1]
  set glb_rblk_top    [expr $tech_pitch_y * 1]
  set glb_rblk_bottom [expr $tech_pitch_y * 1]
  set glb_rblk_llx [expr $glb_x_loc]
  set glb_rblk_lly [expr $glb_y_loc - $glb_rblk_bottom]
  set glb_rblk_urx [expr $glb_x_loc + $glb_width]
  set glb_rblk_ury [expr $glb_y_loc + $glb_height + $glb_rblk_top]
  createRouteBlk \
      -name glb_route_block_top_bottom_sig \
      -layer {m1 m2 m3 m4 m6 m8}  \
      -box "$glb_rblk_llx $glb_rblk_lly $glb_rblk_urx $glb_rblk_ury" \
      -exceptpgnet
  
  # top/bottom routing blockage (power, all)
  set glb_rblk_left   [expr $tech_pitch_x * 1 - 0.04]
  set glb_rblk_right  [expr $tech_pitch_x * 1 - 0.04]
  set glb_rblk_top    [expr $tech_pitch_y * 2 - 0.08]
  set glb_rblk_bottom [expr $tech_pitch_y * 2 - 0.08]
  set glb_rblk_llx [expr $glb_x_loc]
  set glb_rblk_lly [expr $glb_y_loc - $glb_rblk_bottom]
  set glb_rblk_urx [expr $glb_x_loc + $glb_width]
  set glb_rblk_ury [expr $glb_y_loc + $glb_height + $glb_rblk_top]
  createRouteBlk \
      -name glb_route_block_top_bottom_pwr \
      -layer {m1 m2 m3 m4 m5 m6 m7 m8}  \
      -box "$glb_rblk_llx $glb_rblk_lly $glb_rblk_urx $glb_rblk_ury" \
      -pgnetonly
  
  # left/right routing blockage (signal: all except m6)
  set glb_rblk_left   [expr $tech_pitch_x * 0.5 - 0.1]
  set glb_rblk_right  [expr $tech_pitch_x * 0.5 - 0.1]
  set glb_rblk_top    [expr $tech_pitch_y * 1]
  set glb_rblk_bottom [expr $tech_pitch_y * 1]
  set glb_rblk_llx [expr $glb_x_loc - $glb_rblk_left]
  set glb_rblk_lly [expr $glb_y_loc]
  set glb_rblk_urx [expr $glb_x_loc + $glb_width + $glb_rblk_right]
  set glb_rblk_ury [expr $glb_y_loc + $glb_height]
  createRouteBlk \
      -name glb_route_block_left_right_sig \
      -layer {m1 m2 m3 m4 m5 m7 m8}  \
      -box "$glb_rblk_llx $glb_rblk_lly $glb_rblk_urx $glb_rblk_ury" \
      -exceptpgnet
  
  # left/right routing blockage (power, all)
  set glb_rblk_left   [expr $tech_pitch_x * 1 - 0.04]
  set glb_rblk_right  [expr $tech_pitch_x * 1 - 0.04]
  set glb_rblk_top    [expr $tech_pitch_y * 2 - 0.08]
  set glb_rblk_bottom [expr $tech_pitch_y * 2 - 0.08]
  set glb_rblk_llx [expr $glb_x_loc - $glb_rblk_left]
  set glb_rblk_lly [expr $glb_y_loc]
  set glb_rblk_urx [expr $glb_x_loc + $glb_width + $glb_rblk_right]
  set glb_rblk_ury [expr $glb_y_loc + $glb_height]
  createRouteBlk \
      -name glb_route_block_left_right_pwr \
      -layer {m1 m2 m3 m4 m5 m6 m7 m8}  \
      -box "$glb_rblk_llx $glb_rblk_lly $glb_rblk_urx $glb_rblk_ury" \
      -pgnetonly
  
  # # Prevent power vias from blocking pins on GLB (pins on bottom and left edges)
  # set glb_ury [expr $glb_y_loc + $glb_height]
  # set glb_urx [expr $glb_x_loc + $glb_width]
  # set thickness [expr 10 * $vert_pitch]
  # createRouteBlk \
  #   -name glb_top_pg_via_blk \
  #   -cutLayer {4 5 6 7 8 9 10 11 12} \
  #   -pgnetonly \
  #   -box $glb_x_loc $glb_y_loc $glb_urx [expr $glb_y_loc - $thickness]
  
  # createRouteBlk \
  #   -name glb_left_pg_via_blk \
  #   -cutLayer {4 5 6 7 8 9 10 11 12} \
  #   -pgnetonly \
  #   -box [expr $glb_x_loc - $thickness] $glb_y_loc $glb_x_loc $glb_ury
  
  # # Prevent vias to PMESH_BOT_LAYER stripes over GLB
  # createRouteBlk \
  #   -name glb_pmesh_bot_via \
  #   -cutLayer [expr $ADK_POWER_MESH_BOT_LAYER + 1]\
  #   -pgnetonly \
  #   -box $glb_x_loc $glb_y_loc $glb_urx $glb_ury
  
  # # Prevent PMESH_BOT_LAYER stripes over GLB
  # createRouteBlk \
  #   -name glb_pmesh_bot \
  #   -layer $ADK_POWER_MESH_BOT_LAYER \
  #   -pgnetonly \
  #   -box [expr $glb_x_loc + (8*$hori_pitch)] $glb_y_loc [expr $glb_urx - (8*$hori_pitch)] $glb_ury
  
  # # Prevent PMESH_TOP_LAYER stripes over GLB
  # createRouteBlk \
  #   -name glb_pmesh_top \
  #   -layer $ADK_POWER_MESH_TOP_LAYER \
  #   -pgnetonly \
  #   -box $glb_x_loc [expr $glb_y_loc + (2*$vert_pitch)] $glb_urx [expr $glb_ury - (2*$vert_pitch)]
}

##############################################################################
###                         Placing SoC SRAMs                              ###
##############################################################################
set dclk [get_cells -hier -filter {ref_lib_cell_name==diffclock_rx_1v2}]
set dclk_name [get_property $dclk hierarchical_name]
set dclk_width [dbGet [dbGet -p top.insts.name $dclk_name -i 0].cell.size_x]
set dclk_height [dbGet [dbGet -p top.insts.name $dclk_name -i 0].cell.size_y]

set srams [get_cells -hier -filter {is_memory_cell==true}]
set sram_name [get_property [index_collection $srams 0] hierarchical_name]
set sram_width [dbGet [dbGet -p top.insts.name $sram_name -i 0].cell.size_x]
set sram_height [dbGet [dbGet -p top.insts.name $sram_name -i 0].cell.size_y]
set num_of_srams 8
set core_width [dbGet top.fPlan.coreBox_sizex]
# set sram_gap [expr ($core_width - ($num_of_srams * $sram_width)) / ($num_of_srams + 1)]
set sram_gap [expr ($core_width - ($num_of_srams * $sram_width) - $dclk_width) / ($num_of_srams + 2)]
set sram_loc_x [expr $sram_gap + [dbGet top.fPlan.coreBox_llx]]
set sram_loc_y [expr [dbGet top.fPlan.coreBox_ury] - 69.12 - $sram_height]
set sram_loc_y [snap_to_grid $sram_loc_y $vert_pitch]
set sram_loc_y [expr $sram_loc_y - $vert_pitch]

set s 0
foreach_in_collection sram $srams {

  # get sram properties
  set sram_name [get_property $sram full_name]
  set sram_obj [dbGet -p top.insts.name $sram_name]
  
  # snap the sram to the grid, and place it
  set sram_x_loc_snap [snap_to_grid $sram_loc_x $hori_pitch]
  set sram_y_loc_snap [snap_to_grid $sram_loc_y $vert_pitch]
  placeinstance $sram_name $sram_x_loc_snap $sram_y_loc_snap -fixed

  # add halo/routeblk to the sram
  set halo_left   $tech_pitch_x
  set halo_bottom $tech_pitch_y 
  set halo_right  $tech_pitch_x 
  set halo_top    [expr $tech_pitch_y + $vert_pitch]
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
  set sram_loc_x [expr $sram_loc_x + $sram_width + $sram_gap]
  if { $s == 3 } {
    set dclk [get_cells -hier -filter {ref_lib_cell_name==diffclock_rx_1v2}]
    set dclk_name [get_property $dclk hierarchical_name]
    set dclk_width [dbGet [dbGet -p top.insts.name $dclk_name -i 0].cell.size_x]
    set dclk_height [dbGet [dbGet -p top.insts.name $dclk_name -i 0].cell.size_y]
    set dclk_x_loc [snap_to_grid [expr $sram_loc_x - 10] $tech_pitch_x]
    set dclk_y_loc [snap_to_grid 3764 $tech_pitch_y]
    placeinstance $dclk_name $dclk_x_loc $dclk_y_loc -fixed
    addHaloToBlock \
        [expr $tech_pitch_x * 4] \
        [expr $tech_pitch_y * 8] \
        [expr $tech_pitch_x * 4] \
        [expr $tech_pitch_y * 2] \
        $dclk_name \
        -snapToSite
    set dclk_rblk_left   [expr $tech_pitch_x * 4]
    set dclk_rblk_right  [expr $tech_pitch_x * 4]
    set dclk_rblk_top    [expr $tech_pitch_y * 2]
    set dclk_rblk_bottom [expr $tech_pitch_y * 8]
    set dclk_rblk_llx [expr $dclk_x_loc - $dclk_rblk_left]
    set dclk_rblk_lly [expr $dclk_y_loc - $dclk_rblk_bottom]
    set dclk_rblk_urx [expr $dclk_x_loc + $dclk_width + $dclk_rblk_right]
    set dclk_rblk_ury [expr $dclk_y_loc + $dclk_height + $dclk_rblk_top]
    createRouteBlk \
        -name dclk_route_block_pwr \
        -layer {m1 m2 m3 m4 m5 m6 m7 m8 gmz gm0 gmb}  \
        -box "$dclk_rblk_llx $dclk_rblk_lly $dclk_rblk_urx $dclk_rblk_ury" \
        -pgnetonly
    createRouteBlk \
        -name dclk_route_block_sig \
        -layer {gmb}  \
        -box "$dclk_rblk_llx $dclk_rblk_lly $dclk_rblk_urx $dclk_rblk_ury" \
        -exceptpgnet
    createRouteBlk \
        -name dclk_route_block_sigall_except_m6 \
        -layer {m1 m2 m3 m4 m5 m7 m8 gmz gm0}  \
        -box "$dclk_rblk_llx $dclk_rblk_lly $dclk_rblk_urx $dclk_rblk_ury" \
        -exceptpgnet
    set sram_loc_x [expr $sram_loc_x + $dclk_width + $sram_gap]
  }
  incr s
}

##############################################################################
###                  Placing Differential Clock Receiver                   ###
##############################################################################
if { $place_diff_clk_rcvr } {
    
    set dclk [get_cells -hier -filter {ref_lib_cell_name==diffclock_rx_1v2}]
    set dclk_name [get_property $dclk hierarchical_name]
    set dclk_width [dbGet [dbGet -p top.insts.name $dclk_name -i 0].cell.size_x]
    set dclk_height [dbGet [dbGet -p top.insts.name $dclk_name -i 0].cell.size_y]

    set dclk_x_loc [snap_to_grid 1906.429 $tech_pitch_x] 
    set dclk_y_loc [snap_to_grid 3810.521 $tech_pitch_y] 
  
    # placeinstance $dclk_name $dclk_x_loc $dclk_y_loc -fixed

    # addHaloToBlock \
    #     [expr $tech_pitch_x * 1] \
    #     [expr $tech_pitch_y * 8] \
    #     [expr $tech_pitch_x * 1] \
    #     [expr $tech_pitch_y * 2] \
    #     $dclk_name \
    #     -snapToSite

    # # top/bottom routing blockage (signal: all except m5)
    # set dclk_rblk_left   [expr $tech_pitch_x * 0.5 - 0.1]
    # set dclk_rblk_right  [expr $tech_pitch_x * 0.5 - 0.1]
    # set dclk_rblk_top    [expr $tech_pitch_y * 1]
    # set dclk_rblk_bottom [expr $tech_pitch_y * 1]
    # set dclk_rblk_llx [expr $dclk_x_loc]
    # set dclk_rblk_lly [expr $dclk_y_loc - $dclk_rblk_bottom]
    # set dclk_rblk_urx [expr $dclk_x_loc + $dclk_width]
    # set dclk_rblk_ury [expr $dclk_y_loc + $dclk_height + $dclk_rblk_top]
    # createRouteBlk \
    #     -name dclk_route_block_top_bottom_sig \
    #     -layer {m1 m2 m3 m4 m6 m7 m8}  \
    #     -box "$dclk_rblk_llx $dclk_rblk_lly $dclk_rblk_urx $dclk_rblk_ury" \
    #     -exceptpgnet
    
    # # top/bottom routing blockage (power, all)
    # set dclk_rblk_left   [expr $tech_pitch_x * 1 - 0.04]
    # set dclk_rblk_right  [expr $tech_pitch_x * 1 - 0.04]
    # set dclk_rblk_top    [expr $tech_pitch_y * 2 - 0.08]
    # set dclk_rblk_bottom [expr $tech_pitch_y * 2 - 0.08]
    # set dclk_rblk_llx [expr $dclk_x_loc]
    # set dclk_rblk_lly [expr $dclk_y_loc - $dclk_rblk_bottom]
    # set dclk_rblk_urx [expr $dclk_x_loc + $dclk_width]
    # set dclk_rblk_ury [expr $dclk_y_loc + $dclk_height + $dclk_rblk_top]
    # createRouteBlk \
    #     -name dclk_route_block_top_bottom_pwr \
    #     -layer {m1 m2 m3 m4 m5 m6 m7 m8}  \
    #     -box "$dclk_rblk_llx $dclk_rblk_lly $dclk_rblk_urx $dclk_rblk_ury" \
    #     -pgnetonly
    
    # # left/right routing blockage (signal: all except m6)
    # set dclk_rblk_left   [expr $tech_pitch_x * 0.5 - 0.1]
    # set dclk_rblk_right  [expr $tech_pitch_x * 0.5 - 0.1]
    # set dclk_rblk_top    [expr $tech_pitch_y * 1]
    # set dclk_rblk_bottom [expr $tech_pitch_y * 1]
    # set dclk_rblk_llx [expr $dclk_x_loc - $dclk_rblk_left]
    # set dclk_rblk_lly [expr $dclk_y_loc]
    # set dclk_rblk_urx [expr $dclk_x_loc + $dclk_width + $dclk_rblk_right]
    # set dclk_rblk_ury [expr $dclk_y_loc + $dclk_height]
    # createRouteBlk \
    #     -name dclk_route_block_left_right_sig \
    #     -layer {m1 m2 m3 m4 m5 m7 m8}  \
    #     -box "$dclk_rblk_llx $dclk_rblk_lly $dclk_rblk_urx $dclk_rblk_ury" \
    #     -exceptpgnet
    
    # # left/right routing blockage (power, all)
    # set dclk_rblk_left   [expr $tech_pitch_x * 1 - 0.04]
    # set dclk_rblk_right  [expr $tech_pitch_x * 1 - 0.04]
    # set dclk_rblk_top    [expr $tech_pitch_y * 2 - 0.08]
    # set dclk_rblk_bottom [expr $tech_pitch_y * 2 - 0.08]
    # set dclk_rblk_llx [expr $dclk_x_loc - $dclk_rblk_left]
    # set dclk_rblk_lly [expr $dclk_y_loc]
    # set dclk_rblk_urx [expr $dclk_x_loc + $dclk_width + $dclk_rblk_right]
    # set dclk_rblk_ury [expr $dclk_y_loc + $dclk_height]
    # createRouteBlk \
    #     -name dclk_route_block_left_right_pwr \
    #     -layer {m1 m2 m3 m4 m5 m6 m7 m8}  \
    #     -box "$dclk_rblk_llx $dclk_rblk_lly $dclk_rblk_urx $dclk_rblk_ury" \
    #     -pgnetonly
}


# Unplace any standard cells that got placed during init. Not sure why they're
# being placed, but they make power stripe generation take forever.
dbSet [dbGet top.insts.cell.baseClass core -p2].pStatus unplaced
