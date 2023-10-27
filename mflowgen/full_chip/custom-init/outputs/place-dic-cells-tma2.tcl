#=========================================================================
# place-dic-cells.tcl
#=========================================================================
# This script places the drop-in cell required by this technology.
# !! This is only used for TMA2 !!
# Author : 
# Date   :

proc snap_to_grid {input granularity} {
   set new_value [expr ceil($input / $granularity) * $granularity]
   return $new_value
}

set hori_pitch [dbGet top.fPlan.coreSite.size_x]
set vert_pitch [dbGet top.fPlan.coreSite.size_y]


for {set x 0} {$x < 4} {incr x} {
    for {set y 0} {$y < 4} {incr y} {
        set loc_x [expr 900*$x]
        set loc_y [expr 900*$y]
        # Place DIC-CD
        set dic_cd_inst_name INTEL_DIC_CD_x${x}_y${y}
        set dic_cd_x [snap_to_grid $loc_x $hori_pitch]
        set dic_cd_y [snap_to_grid $loc_y $vert_pitch]
        set halo_cd_left   [expr $hori_pitch * 5]
        set halo_cd_bottom [expr $vert_pitch * 2]
        set halo_cd_right  [expr $hori_pitch * 5]
        set halo_cd_top    [expr $vert_pitch * 1]
        addInst \
            -cell $ADK_DIC_CELL_CD \
            -inst $dic_cd_inst_name \
            -loc "$dic_cd_x $dic_cd_y" \
            -place_status fixed
        addHaloToBlock \
            $halo_cd_left \
            $halo_cd_bottom \
            $halo_cd_right \
            $halo_cd_top \
            $dic_cd_inst_name \
            -snapToSite
        
        # Place DIC-REG
        set dic_reg_inst_name INTEL_DIC_REG_x${x}_y${y}
        set dic_reg_x [snap_to_grid $loc_x $hori_pitch]
        set dic_reg_y [snap_to_grid [expr $loc_y-100] $vert_pitch]
        set halo_reg_left   [expr $hori_pitch * 5]
        set halo_reg_bottom [expr $vert_pitch * 1]
        set halo_reg_right  [expr $hori_pitch * 5]
        set halo_reg_top    [expr $vert_pitch * 1]
        addInst \
            -cell $ADK_DIC_CELL_REG \
            -inst $dic_reg_inst_name \
            -loc "$dic_reg_x $dic_reg_y" \
            -place_status fixed
        addHaloToBlock \
            $halo_reg_left \
            $halo_reg_bottom \
            $halo_reg_right \
            $halo_reg_top \
            $dic_reg_inst_name \
            -snapToSite
    }
}
    