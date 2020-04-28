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
  set ic2glb_y_dist 400
  set ic2glc_y_dist -200
  # First, get the sizes of all Garnet macros (Interconnect,
  # global_buffer, and global_controller)
  
  set interconnect [get_cells -hier -filter {ref_lib_cell_name==Interconnect}]
  set interconnect_name [get_property $interconnect hierarchical_name]
  set ic_width [dbGet [dbGet -p top.insts.name $interconnect_name -i 0].cell.size_x]
  set ic_height [dbGet [dbGet -p top.insts.name $interconnect_name -i 0].cell.size_y]

  set ic_y_loc [snap_to_grid [expr ([dbGet top.fPlan.box_sizey] - $ic_height)/20.] $vert_pitch]
  set ic_x_loc [snap_to_grid [expr ([dbGet top.fPlan.box_sizex] - $ic_width)/2.] $horiz_pitch]
    
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
  
  set glb [get_cells -hier -filter {ref_lib_cell_name==global_buffer}]
  set glb_name [get_property $glb hierarchical_name]
  set glb_width [dbGet [dbGet -p top.insts.name $glb_name -i 0].cell.size_x]
  set glb_height [dbGet [dbGet -p top.insts.name $glb_name -i 0].cell.size_y]
  
  set glb_y_loc [snap_to_grid [expr $ic_y_loc + $ic_height + ($vert_pitch * $ic2glb_y_dist)] $vert_pitch]
  set glb_x_loc [snap_to_grid [expr ([dbGet top.fPlan.box_sizex] - $glb_width)/2.] $horiz_pitch]
  
  placeinstance $glb_name $glb_x_loc $glb_y_loc -fixed
  addHaloToBlock [expr $horiz_pitch * 3] $vert_pitch [expr $horiz_pitch * 3] $vert_pitch $glb_name -snapToSite
  
  # Prevent power vias from blocking pins on GLB (pins on top and left edges)
  set glb_ury [expr $glb_y_loc + $glb_height]
  set glb_urx [expr $glb_x_loc + $glb_width]
  set thickness [expr 10 * $vert_pitch]
  createRouteBlk \
    -name glb_top_pg_via_blk \
    -layer {VIA3 VIA4 VIA5 VIA6 VIA7} \
    -pgnetonly \
    -box $glb_x_loc $glb_ury $glb_urx [expr $glb_ury + $thickness]
  
  createRouteBlk \
    -name glb_left_pg_via_blk \
    -layer {VIA3 VIA4 VIA5 VIA6 VIA7} \
    -pgnetonly \
    -box [expr $glb_x_loc - $thickness] $glb_y_loc $glb_x_loc $glb_ury
  
  set glc [get_cells -hier -filter {ref_lib_cell_name==global_controller}]
  set glc_name [get_property $glc hierarchical_name]
  set glc_width [dbGet [dbGet -p top.insts.name $glc_name -i 0].cell.size_x]
  set glc_height [dbGet [dbGet -p top.insts.name $glc_name -i 0].cell.size_y]
  set glc_y_loc [snap_to_grid [expr $ic_y_loc + $ic_height + ($vert_pitch * $ic2glc_y_dist)] $vert_pitch]
  set glc_x_loc [snap_to_grid [expr $ic_x_loc - $glc_width - 200] $horiz_pitch]
  
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
set sram_width [dbGet [dbGet -p top.insts.name *mem_inst* -i 0].cell.size_x]
set sram_height [dbGet [dbGet -p top.insts.name *mem_inst* -i 0].cell.size_y]

# SRAM Placement params
# SRAMs are abutted vertically
set sram_spacing_y 0
# We can abut sides of SRAMS with no pins
set sram_spacing_x_odd 0
# Set spacing between pinned sides of SRAMs to some 
# reasonable number of pitches
set sram_spacing_x_even [expr 200 * $horiz_pitch]
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

set sram_start_y [snap_to_grid [expr ([dbGet top.fPlan.box_sizey] - $block_height)/6.] $vert_pitch]
set sram_start_x [snap_to_grid [expr ([dbGet top.fPlan.box_sizex] - $block_width)/10.] $horiz_pitch]

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
  # Create M3 pg net blockage to prevent DRC from interaction
  # with M5 stripes
  set llx [dbGet [dbGet -p top.insts.name $sram_name].box_llx]
  set lly [dbGet [dbGet -p top.insts.name $sram_name].box_lly]
  set urx [dbGet [dbGet -p top.insts.name $sram_name].box_urx]
  set ury [dbGet [dbGet -p top.insts.name $sram_name].box_ury]
  set tb_margin $vert_pitch
  set lr_margin [expr $horiz_pitch * 3]
  addHaloToBlock [expr $horiz_pitch * 3] $vert_pitch [expr $horiz_pitch * 3] $vert_pitch $sram_name -snapToSite
  createRouteBlk \
    -inst $sram_name \
    -box [expr $llx - $lr_margin] [expr $lly - $tb_margin] [expr $urx + $lr_margin] [expr $ury + $tb_margin] \
    -layer 3 \
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

