#=========================================================================
# floorplan.tcl
#=========================================================================
# This script is called from the Innovus init flow step to place all
# macros in the full chip floorplan
#
# Author : Alex Carsello
# Date   : March 19,2020

# First, get the sizes of all Garnet macros (Interconnect,
# global_buffer, and global_controller)

set vert_pitch [dbGet top.fPlan.coreSite.size_y]
set horiz_pitch [dbGet top.fPlan.coreSite.size_x]

# Place SRAMS
set horiz_pitch [dbGet top.fPlan.coreSite.size_x]
set vert_pitch [dbGet top.fPlan.coreSite.size_y]
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
set sram_start_x [snap_to_grid [expr ([dbGet top.fPlan.box_sizex] - $block_width)/6.] $horiz_pitch]

set y_loc $sram_start_y
set x_loc $sram_start_x
set col 0
set row 0
foreach_in_collection sram $srams {
  set sram_name [get_property $sram full_name]
  if {[expr $col % 2] == 1} {
    placeInstance $sram_name $x_loc $y_loc MY -fixed
  } else {
    placeInstance $sram_name $x_loc $y_loc -fixed
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

