#=========================================================================
# place-glb-top.tcl
#=========================================================================
#
# Author : Po-Han Chen
# Date   : 

proc snap_to_grid {input granularity} {
   set new_value [expr ceil($input / $granularity) * $granularity]
   return $new_value
}

set hori_pitch [dbGet top.fPlan.coreSite.size_x]
set vert_pitch [dbGet top.fPlan.coreSite.size_y]
set tech_pitch_x [expr 5 * $hori_pitch]
set tech_pitch_y [expr 1 * $vert_pitch]

#-------------------------------------------------------------------------
# Collect Tile Information
#-------------------------------------------------------------------------
# GLB placement prep
set glb [get_cells -hier -filter {ref_lib_cell_name==global_buffer}]
set glb_name [get_property $glb hierarchical_name]
set glb_width [dbGet [dbGet -p top.insts.name $glb_name -i 0].cell.size_x]
set glb_height [dbGet [dbGet -p top.insts.name $glb_name -i 0].cell.size_y]
# set glb_x_loc [snap_to_grid [expr ([dbGet top.fPlan.box_sizex] - $glb_width)/2.] $pmesh_top_pitch]
# set glb_y_loc [snap_to_grid [expr $ic_y_loc + $ic_height + ($vert_pitch * $ic2glb_y_dist)] $pmesh_bot_pitch]
# set glb_x_loc [snap_to_grid 102.06 $tech_pitch_x]
set glb_x_loc [snap_to_grid 99.36 $tech_pitch_x]
set glb_y_loc [snap_to_grid 3190 $tech_pitch_y]
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

# Signal routing blockage
set glb_llx [dbGet [dbGet -p top.insts.name $glb_name].box_llx]
set glb_lly [dbGet [dbGet -p top.insts.name $glb_name].box_lly]
set glb_urx [dbGet [dbGet -p top.insts.name $glb_name].box_urx]
set glb_ury [dbGet [dbGet -p top.insts.name $glb_name].box_ury]
createRouteBlk \
    -inst $glb_name \
    -name glb_rblk_sig_non_pin_layers \
    -layer {m1 m2    m4 m5 m6    m8 }  \
    -cover \
    -spacing 0.48 \
    -exceptpgnet

createRouteBlk \
    -inst $glb_name \
    -name glb_rblk_sig_pin_layers \
    -layer {      m3          m7   }  \
    -cover \
    -exceptpgnet

createRouteBlk \
    -name glb_rblk_sig_pin_layers_left_right \
    -layer {      m3          m7   }  \
    -box [expr $glb_llx - 0.48] $glb_lly [expr $glb_urx + 0.48] $glb_ury \
    -exceptpgnet

# Power routing blockage
createRouteBlk \
    -inst $glb_name \
    -name glb_route_block_top_bottom_pwr \
    -layer {m1 m2 m3 m4 m5 m6 m7 m8}  \
    -cover \
    -spacing 0.48 \
    -pgnetonly
