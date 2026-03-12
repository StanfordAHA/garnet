#=========================================================================
# place-matrix-unit.tcl
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
# Matrix Unit Placement
#-------------------------------------------------------------------------
# MU placement prep
set mu [get_cells -hier -filter {ref_lib_cell_name==MatrixUnitWrapper}]
set mu_name [get_property $mu hierarchical_name]
set mu_width [dbGet [dbGet -p top.insts.name $mu_name -i 0].cell.size_x]
set mu_height [dbGet [dbGet -p top.insts.name $mu_name -i 0].cell.size_y]
# set mu_x_loc [snap_to_grid 100 $tech_pitch_x]
set mu_x_loc [snap_to_grid 250 $tech_pitch_x]
set mu_y_loc [snap_to_grid 120 $tech_pitch_y]
# Place mu
placeinstance $mu_name $mu_x_loc $mu_y_loc -fixed
# addHaloToBlock [expr $hori_pitch * 15] $vert_pitch [expr $hori_pitch * 3] $vert_pitch $mu_name -snapToSite
addHaloToBlock \
    [expr $tech_pitch_x * 1] \
    [expr $tech_pitch_y * 2] \
    [expr $tech_pitch_x * 1] \
    [expr $tech_pitch_y * 2] \
    $mu_name \
    -snapToSite

# Signal routing blockage
createRouteBlk \
    -inst $mu_name \
    -name mu_rblk_sig_non_pin_layers \
    -layer {m1 m2    m4 m5 m6 m7 m8}  \
    -cover \
    -spacing 0.24 \
    -exceptpgnet
createRouteBlk \
    -inst $mu_name \
    -name mu_rblk_sig_pin_layers \
    -layer {      m3               }  \
    -cover \
    -exceptpgnet

# Power routing blockage
createRouteBlk \
    -inst $mu_name \
    -name mu_route_block_top_bottom_pwr \
    -layer {m1 m2 m3 m4 m5 m6 m7 m8}  \
    -cover \
    -spacing 0.48 \
    -pgnetonly

# place DIC REG cells to make DRC happy
set dic_reg_x [snap_to_grid [expr $mu_x_loc + $mu_width + 20] $tech_pitch_x]
set halo_dic_reg_left   [expr $hori_pitch * 5]
set halo_dic_reg_bottom [expr $vert_pitch * 1]
set halo_dic_reg_right  [expr $hori_pitch * 5]
set halo_dic_reg_top    [expr $vert_pitch * 1]

set dic_name  INTEL_FULLCHIP_DIC_REG_0
set dic_reg_y [snap_to_grid 2900 $vert_pitch]
addInst \
    -cell $ADK_DIC_CELL_REG \
    -inst $dic_name \
    -loc "$dic_reg_x $dic_reg_y" \
    -place_status fixed
addHaloToBlock \
    $halo_dic_reg_left \
    $halo_dic_reg_bottom \
    $halo_dic_reg_right \
    $halo_dic_reg_top \
    $dic_name \
    -snapToSite

set dic_name  INTEL_FULLCHIP_DIC_REG_1
set dic_reg_y [snap_to_grid 1500 $vert_pitch]
addInst \
    -cell $ADK_DIC_CELL_REG \
    -inst $dic_name \
    -loc "$dic_reg_x $dic_reg_y" \
    -place_status fixed
addHaloToBlock \
    $halo_dic_reg_left \
    $halo_dic_reg_bottom \
    $halo_dic_reg_right \
    $halo_dic_reg_top \
    $dic_name \
    -snapToSite

set dic_name  INTEL_FULLCHIP_DIC_REG_2
set dic_reg_y [snap_to_grid 100 $vert_pitch]
addInst \
    -cell $ADK_DIC_CELL_REG \
    -inst $dic_name \
    -loc "$dic_reg_x $dic_reg_y" \
    -place_status fixed
addHaloToBlock \
    $halo_dic_reg_left \
    $halo_dic_reg_bottom \
    $halo_dic_reg_right \
    $halo_dic_reg_top \
    $dic_name \
    -snapToSite
