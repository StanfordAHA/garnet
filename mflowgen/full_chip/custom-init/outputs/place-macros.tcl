#=========================================================================
# floorplan.tcl
#=========================================================================
# This script is called from the Innovus init flow step to place all
# macros in the full chip floorplan
#
# Author : Alex Carsello
# Date   : March 19,2020
set vert_pitch [dbGet top.fPlan.coreSite.size_y]
set horiz_pitch [dbGet top.fPlan.coreSite.size_x]

if { ! $::env(soc_only) } {
  # Params
  # Vertical distance (in # pitches) betwween GLB and Tile array
  set ic2glb_y_dist 330
  set ic2glc_y_dist 600

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

  set ic_y_loc [snap_to_grid [expr ([dbGet top.fPlan.box_sizey] - $ic_height)/20.] $pmesh_bot_pitch]
  set ic_x_loc [snap_to_grid [expr ([dbGet top.fPlan.box_sizex] - $ic_width)/2.] $pmesh_top_pitch]
    
  placeinstance $interconnect_name $ic_x_loc $ic_y_loc -fixed
  addHaloToBlock [expr $horiz_pitch * 3] $vert_pitch [expr $horiz_pitch * 3] $vert_pitch $interconnect_name -snapToSite

  # Prevent power vias from blocking pins on interconnect (all pins on top edge)
  set ic_ury [expr $ic_y_loc + $ic_height]
  set ic_urx [expr $ic_x_loc + $ic_width]
  set thickness [expr 10 * $vert_pitch]
  createRouteBlk \
    -name ic_top_pg_via_blk \
    -layer {VIA3 VIA4 VIA5 VIA6 VIA7} \
    -pgnetonly \
    -box $ic_x_loc $ic_ury $ic_urx [expr $ic_ury + $thickness]

  # Prevent PMESH_BOT_LAYER stripes over IC
  createRouteBlk \
    -name ic_pmesh_bot_via \
    -layer VIA$ADK_POWER_MESH_BOT_LAYER \
    -pgnetonly \
    -box $ic_x_loc $ic_y_loc $ic_urx $ic_ury
  
  createRouteBlk \
    -name ic_pmesh_bot \
    -layer $ADK_POWER_MESH_BOT_LAYER \
    -pgnetonly \
    -box [expr $ic_x_loc + (8*$horiz_pitch)] $ic_y_loc [expr $ic_urx - (8*$horiz_pitch)] $ic_ury
  
  # GLB placement prep
  set glb [get_cells -hier -filter {ref_lib_cell_name==global_buffer}]
  set glb_name [get_property $glb hierarchical_name]
  set glb_width [dbGet [dbGet -p top.insts.name $glb_name -i 0].cell.size_x]
  set glb_height [dbGet [dbGet -p top.insts.name $glb_name -i 0].cell.size_y]

  set glb_y_loc [snap_to_grid [expr $ic_y_loc + $ic_height + ($vert_pitch * $ic2glb_y_dist)] $pmesh_bot_pitch]
  set glb_x_loc [snap_to_grid [expr ([dbGet top.fPlan.box_sizex] - $glb_width)/2.] $pmesh_top_pitch]
  
  ##############################################################################
  # Lots of congestion to the left of GLB where there are SRAMs and such.
  # But nothing on the right side of the GLB really.
  # So I moved the lone lower-alignment-cell from right side of GLB to
  # left side (see alignment-cells.tcl), giving us room to move GLB to
  # the right, away from the congested area.
  # Currently adding ~ 300u (3300 horiz pitches), probably more than needed.
  set glb_x_loc [ expr $glb_x_loc + (3300 * $horiz_pitch) ]
  set glb_x_loc [ snap_to_grid $glb_x_loc $pmesh_bot_pitch ]
  
  # Place GLB
  placeinstance $glb_name $glb_x_loc $glb_y_loc -fixed
  addHaloToBlock [expr $horiz_pitch * 3] $vert_pitch [expr $horiz_pitch * 3] $vert_pitch $glb_name -snapToSite
  
  # Prevent power vias from blocking pins on GLB (pins on bottom and left edges)
  set glb_ury [expr $glb_y_loc + $glb_height]
  set glb_urx [expr $glb_x_loc + $glb_width]
  set thickness [expr 10 * $vert_pitch]
  createRouteBlk \
    -name glb_top_pg_via_blk \
    -layer {VIA3 VIA4 VIA5 VIA6 VIA7} \
    -pgnetonly \
    -box $glb_x_loc $glb_y_loc $glb_urx [expr $glb_y_loc - $thickness]
  
  createRouteBlk \
    -name glb_left_pg_via_blk \
    -layer {VIA3 VIA4 VIA5 VIA6 VIA7} \
    -pgnetonly \
    -box [expr $glb_x_loc - $thickness] $glb_y_loc $glb_x_loc $glb_ury
  
  # Prevent PMESH_BOT_LAYER stripes over GLB
  createRouteBlk \
    -name glb_pmesh_bot_via \
    -layer VIA$ADK_POWER_MESH_BOT_LAYER \
    -pgnetonly \
    -box $glb_x_loc $glb_y_loc $glb_urx $glb_ury
  
  createRouteBlk \
    -name glb_pmesh_bot \
    -layer $ADK_POWER_MESH_BOT_LAYER \
    -pgnetonly \
    -box [expr $glb_x_loc + (8*$horiz_pitch)] $glb_y_loc [expr $glb_urx - (8*$horiz_pitch)] $glb_ury
  
  # Place GLB controller
  set glc [get_cells -hier -filter {ref_lib_cell_name==global_controller}]
  set glc_name [get_property $glc hierarchical_name]
  set glc_width [dbGet [dbGet -p top.insts.name $glc_name -i 0].cell.size_x]
  set glc_height [dbGet [dbGet -p top.insts.name $glc_name -i 0].cell.size_y]
  set glc_y_loc [snap_to_grid [expr $ic_y_loc + $ic_height + ($vert_pitch * $ic2glc_y_dist)] $pmesh_bot_pitch]
  set glc_x_loc [snap_to_grid [expr $ic_x_loc + 100] $pmesh_top_pitch]
  
  placeinstance $glc_name $glc_x_loc $glc_y_loc -fixed
  addHaloToBlock [expr $horiz_pitch * 3] $vert_pitch [expr $horiz_pitch * 3] $vert_pitch $glc_name -snapToSite
  
  # Prevent power vias from blocking pins on GLC (pins on right and left edges)
  set glc_ury [expr $glc_y_loc + $glc_height]
  set glc_urx [expr $glc_x_loc + $glc_width]
  set thickness [expr 10 * $vert_pitch]  
  createRouteBlk \
    -name glc_left_pg_via_blk \
    -layer {VIA3 VIA4 VIA5 VIA6 VIA7} \
    -pgnetonly \
    -box [expr $glc_x_loc - $thickness] $glc_y_loc $glc_x_loc $glc_ury
  
  createRouteBlk \
    -name glc_right_pg_via_blk \
    -layer {VIA3 VIA4 VIA5 VIA6 VIA7} \
    -pgnetonly \
    -box $glc_x_loc $glc_y_loc [expr $glc_urx + $thickness] $glc_ury
}
# Place SRAMS
set srams [get_cells -hier -filter {is_memory_cell==true}]
set sram_name [get_property [index_collection $srams 0] hierarchical_name]
set sram_width [dbGet [dbGet -p top.insts.name $sram_name -i 0].cell.size_x]
set sram_height [dbGet [dbGet -p top.insts.name $sram_name -i 0].cell.size_y]

# SRAM Placement params
# SRAMs are abutted vertically
set sram_spacing_y 0
# We can abut sides of SRAMS with no pins
set sram_spacing_x_odd 0
# Set spacing between pinned sides of SRAMs to some 
# reasonable number of pitches
set sram_spacing_x_even [expr 200 * $horiz_pitch]

# Lots of congestion around the SRAMs. Keep getting routing errors in
# this area. So let's add some space to help it out.
set sram_spacing_y      [expr 100 * $vert_pitch]
set sram_spacing_x_odd  [expr 400 * $horiz_pitch]
set sram_spacing_x_even [expr 400 * $horiz_pitch]

# Parameter for how many SRAMs to stack vertically
set bank_height 4

# Center the SRAMs within the core area of the tile
set num_banks [expr [sizeof_collection $srams] / $bank_height]
set num_spacings [expr $num_banks - 1]
set num_even_spacings [expr int(ceil($num_spacings/2.0))]
set num_odd_spacings [expr $num_spacings/2]
set total_spacing_width [expr ($num_odd_spacings * $sram_spacing_x_odd) + ($num_even_spacings * $sram_spacing_x_even)]
set block_width [expr ($num_banks * $sram_width) + $total_spacing_width]
set block_height [expr ($sram_height * $bank_height) + ($sram_height * ($bank_height - 1))]

set sram_start_y [snap_to_grid [expr ([dbGet top.fPlan.box_sizey] - $block_height) * 0.75] $vert_pitch]
set sram_start_x [snap_to_grid [expr ([dbGet top.fPlan.box_sizex] - $block_width)/15.] $horiz_pitch]

set y_loc $sram_start_y
set x_loc $sram_start_x
set col 0
set row 0
foreach_in_collection sram $srams {
  set sram_name [get_property $sram full_name]
  if {[expr $col % 2] == 1} {
    placeInstance $sram_name $x_loc $y_loc MY -fixed
  } else {
    placeinstance $sram_name $x_loc $y_loc -fixed
  }
  # Create M1,M3 pg net blockage to prevent DRC from interaction
  # with M5 stripes or pgnet short with sram pins
  set llx [dbGet [dbGet -p top.insts.name $sram_name].box_llx]
  set lly [dbGet [dbGet -p top.insts.name $sram_name].box_lly]
  set urx [dbGet [dbGet -p top.insts.name $sram_name].box_urx]
  set ury [dbGet [dbGet -p top.insts.name $sram_name].box_ury]
  set tb_margin $vert_pitch
  set lr_margin [expr $horiz_pitch * 3]
  addHaloToBlock $lr_margin $tb_margin $lr_margin $tb_margin $sram_name -snapToSite
  # Make routing blockage smaller than halo so that endcaps are not obstructed by M1 blockage
  createRouteBlk \
    -inst $sram_name \
    -box [expr $llx - (0.8 * $lr_margin)] [expr $lly - (0.8 * $tb_margin)] [expr $urx + (0.8 * $lr_margin)] [expr $ury + (0.8 * $tb_margin)] \
    -layer [list 1 3] \
    -pgnetonly
  set row [expr $row + 1]
  set y_loc [expr $y_loc + $sram_height + $sram_spacing_y]
  # Next column over
  if {$row >= $bank_height} {
    set row 0
    if {[expr $col % 2] == 0} {
      set sram_spacing_x $sram_spacing_x_even
    } else {
      set sram_spacing_x $sram_spacing_x_odd
    }
    set x_loc [expr $x_loc + $sram_width + $sram_spacing_x]
    set y_loc $sram_start_y
    set col [expr $col + 1]
  }
}

# Place analog block
# placeInstance iphy 1352.685 4098.000 -fixed ; # dragonphy
  placeInstance iphy 1703.075 4098.000 -fixed ; # dragonphy2 11/2020

# Create route Blockage over dragonphy
set llx [dbGet [dbGet -p top.insts.name iphy].box_llx]
set lly [dbGet [dbGet -p top.insts.name iphy].box_lly]
set urx [dbGet [dbGet -p top.insts.name iphy].box_urx]
set ury [dbGet [dbGet -p top.insts.name iphy].box_ury]

createRouteBlk \
  -box [expr $llx - 5] [expr $lly - 5] [expr $urx + 5] [expr $ury + (3 * $vert_pitch)] \
  -layer {3 9} \
  -name dragonphy \
  -pgnetonly

set halo_margin [expr 3 * $vert_pitch]
addHaloToBlock $halo_margin $halo_margin $halo_margin $halo_margin  iphy


# Skip routing on all analog nets

set_db [get_db nets ext_clk_async_p] .skip_routing true
set_db [get_db nets ext_clk_async_n] .skip_routing true
set_db [get_db nets ext_clkn] .skip_routing true
set_db [get_db nets ext_clkp] .skip_routing true
set_db [get_db nets ext_Vcm] .skip_routing true
set_db [get_db nets ext_Vcal] .skip_routing true
set_db [get_db nets ext_mdll_clk_refp] .skip_routing true
set_db [get_db nets ext_mdll_clk_refn] .skip_routing true
set_db [get_db nets ext_mdll_clk_monp] .skip_routing true
set_db [get_db nets ext_mdll_clk_monn] .skip_routing true
set_db [get_db nets ext_rx_inp] .skip_routing true
set_db [get_db nets ext_rx_inn] .skip_routing true
set_db [get_db nets ext_rx_inp_test] .skip_routing true
set_db [get_db nets ext_rx_inn_test] .skip_routing true
set_db [get_db nets clk_out_p] .skip_routing true
set_db [get_db nets clk_out_n] .skip_routing true
set_db [get_db nets clk_trig_p] .skip_routing true
set_db [get_db nets clk_trig_n] .skip_routing true

# Unplace any standard cells that got placed during init. Not sure why they're
# being placed, but they make power stripe generation take forever.
dbSet [dbGet top.insts.cell.baseClass core -p2].pStatus unplaced
