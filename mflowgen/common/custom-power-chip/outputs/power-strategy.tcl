#=========================================================================
# power-strategy.tcl
#=========================================================================
# This script implements a full power mesh for a sub-block design. In sub-
# block design, we use {m1, m2, ..., m7, m8, gmz} to create power grids.
# In chip top design, we use {gm0, gmb} to create top level power grids.
# This strategy allows easy integration by simply dropping down Vias from
# gm0 (chip top) to gmz (sub-block). Note that M1 stdcell power rails are
# horizontal and M2 preferred routing direction is also horizontal. Hence,
# we create M2 power stripes directly on top of M1 (fully overlapped) and
# put via staples along them.
# 
# Author : Po-Han Chen
# Date   : November 24, 2023

#-------------------------------------------------------------------------
# Shorter names from the ADK
#-------------------------------------------------------------------------

set pmesh_bot $ADK_POWER_MESH_BOT_LAYER
set pmesh_top $ADK_POWER_MESH_TOP_LAYER

#-------------------------------------------------------------------------
# M1/M2 power staples
#-------------------------------------------------------------------------
set m1_rail_width [dbGet [dbGet -p top.nets.swires.shape followpin].width]
set m1_rail_width [lindex $m1_rail_width 0]
set poly_pitch [dbGet top.fPlan.coreSite.size_x]

# At the design level, the expectation is that M2 should be fully strapped
# on power M1 with V1 placed every alternate poly pitch
set v1_x_pitch [expr $poly_pitch * 4]
set v1_x_offset_vss [expr $poly_pitch * 2]
set v1_x_offset_vdd [expr $poly_pitch * 3]

# m1.  PG grid creation should be done after well tap insertion. This way, the
#  route_special command can auto detect the m1 power and ground pins and draw the required stripes.
sroute \
    -nets {VSS VDD} \
    -connect corePin \
    -corePinLayer m1 \
    -corePinTarget none

# m2. we run edit_duplicate_routes instead of add_stripe so that m2 stripes follow
#   m1 stripe pattern dictated by standard cell row heights.
#   This allows the same PG grid creation code to work for any library used.
deselect_obj -all
editSelect -shape FOLLOWPIN -layer m1
editDuplicate -layer_horizontal m2
deselect_obj -all

# now connect parallel m1 and m2 layers with a via1 aligned to m1 tracks
setViaGenMode -reset
# setViaGenMode -ignore_DRC true
editPowerVia \
    -bottom_layer m1 \
    -top_layer m2 \
    -nets {VDD VSS} \
    -add_vias 1 \
    -orthogonal_only 0 \
    -split_long_via { 1 0.432 0.432 }

#-------------------------------------------------------------------------
# Power Mesh (m2 to gmz)
#-------------------------------------------------------------------------
set prev_layer m2
set i 0
foreach layer { m3 m4 m5 m6 m7 m8 gmz } {

    # configure via gen
    if { $layer == "m5" } {
        setViaGenMode -reset
        setViaGenMode -viarule_preference predefined
        setViaGenMode -preferred_vias_only open
        setViaGenMode -ignore_DRC false
    } else {
        setViaGenMode -reset
        setViaGenMode -viarule_preference default
        setViaGenMode -ignore_DRC false
    }
    
    # configure stripe gen
    setAddStripeMode -reset
    setAddStripeMode -ignore_DRC false
    setAddStripeMode -stacked_via_bottom_layer $prev_layer \
                     -stacked_via_top_layer    $layer
    
    # determine stripe direction
    if { $layer == "m3" || $layer == "m5" || $layer == "m7" || $layer == "gmz"} {
        set stripe_direction vertical
    } else {
        set stripe_direction horizontal
    }

    # determine stripe parameters
    set stripe_width          [lindex $ADK_M3_TO_M8_STRIPE_WIDTH_LIST $i]
    set stripe_offset         [lindex $ADK_M3_TO_M8_STRIPE_OFSET_LIST $i]
    set stripe_spacing        [lindex $ADK_M3_TO_M8_STRIPE_SPACE_LIST $i]
    set stripe_interset_pitch [expr 2 * ($stripe_width + $stripe_spacing)]

    # create the stripes
    addStripe \
        -nets                {VSS VDD} \
        -layer               $layer \
        -direction           $stripe_direction \
        -width               $stripe_width \
        -start_offset        $stripe_offset \
        -spacing             $stripe_spacing \
        -set_to_set_distance $stripe_interset_pitch

    # update previous metal layer
    set prev_layer $layer
    set i [expr $i + 1]

}

#-------------------------------------------------------------------------
# RDL Power Mesh (gm0)
#-------------------------------------------------------------------------
# create routing blockage on cut layer to prevent
set core_llx [dbGet top.fPlan.coreBox_llx]
set core_lly [dbGet top.fPlan.coreBox_lly]
set core_urx [dbGet top.fPlan.coreBox_urx]
set core_ury [dbGet top.fPlan.coreBox_ury]
createRouteBlk \
    -name RDL_BLOCKAGE_TEMP \
    -cutLayer gv0 \
    -box "$core_llx $core_lly $core_urx $core_ury"


set vert_pitch [dbGet top.fPlan.coreSite.size_y]
set hori_pitch [dbGet top.fPlan.coreSite.size_x]

set pwr_gm0_width   2.0
set pwr_gm0_spacing 4.0
set pwr_gm0_offset  [expr $pwr_gm0_spacing + 0.5 * $pwr_gm0_width]
set pwr_gm0_interset_pitch [expr 2 * ($pwr_gm0_width + $pwr_gm0_spacing)]

setViaGenMode -reset
setViaGenMode -viarule_preference default
setViaGenMode -ignore_DRC false

setAddStripeMode -reset
setAddStripeMode -ignore_DRC false
setAddStripeMode -stacked_via_bottom_layer gmz \
                 -stacked_via_top_layer    gm0

addStripe \
        -nets                {VSS VDD} \
        -layer               gm0 \
        -direction           horizontal \
        -width               $pwr_gm0_width \
        -start_offset        $pwr_gm0_offset \
        -spacing             $pwr_gm0_spacing \
        -set_to_set_distance $pwr_gm0_interset_pitch

#-------------------------------------------------------------------------
# RDL Power Mesh (gmb)
#-------------------------------------------------------------------------
deleteRouteBlk -name RDL_BLOCKAGE_TEMP

set pwr_gmb_width [dbGet [dbGet -p head.layers.name gmb].maxWidth]
set pwr_gmb_offset 0
set pwr_gmb_spacing 65.976
set pwr_gmb_interset_pitch [expr 2 * ($pwr_gmb_width + $pwr_gmb_spacing)]

set pwr_area_llx 552.792
set pwr_area_lly 852.66
set pwr_area_urx [expr [dbGet top.fPlan.box_urx] - $pwr_area_llx]
set pwr_area_ury [expr [dbGet top.fPlan.box_ury] - $pwr_area_lly]

setViaGenMode -reset
setViaGenMode -viarule_preference default
setViaGenMode -ignore_DRC false

setAddStripeMode -reset
setAddStripeMode -ignore_DRC false
setAddStripeMode -stacked_via_bottom_layer gm0 \
                 -stacked_via_top_layer    gmb

addStripe \
        -nets                {VSS VDD} \
        -layer               gmb \
        -direction           vertical \
        -area                "$pwr_area_llx $pwr_area_lly $pwr_area_urx $pwr_area_ury" \
        -width               $pwr_gmb_width \
        -start_offset        $pwr_gmb_offset \
        -spacing             $pwr_gmb_spacing \
        -set_to_set_distance $pwr_gmb_interset_pitch

#-------------------------------------------------------------------------
# Manually route power from bumps to pads
#-------------------------------------------------------------------------
uiSetTool addWire

setEditMode -type special
setEditMode -shape None
setEditMode -layer_horizontal gmb
setEditMode -layer_vertical gmb
setEditMode -width_horizontal 8
setEditMode -width_vertical 8
setEditMode -spacing_vertical 1
setEditMode -spacing_horizontal 1
setEditMode -allow_45_degree 1
setEditMode -create_via_on_pin 1

setEditMode -create_crossover_vias 0

# TOP (left to right)
setEditMode -nets VSS
editAddRoute 248.229 3766.17
editAddRoute 246.194 3815.52
editAddRoute 227.881 3856.21
editAddRoute 210.586 4013.4
editCommitRoute 210.586 4013.4
setEditMode -create_crossover_vias 1
editAddRoute 208.551 4011.87
editAddRoute 212.62 4063.76
editCommitRoute 212.62 4063.76
setEditMode -create_crossover_vias 0

setEditMode -nets VSS
editAddRoute 249.755 3920.82
editAddRoute 253.825 3958.46
editAddRoute 255.859 3971.68
editAddRoute 264.507 3973.72
editAddRoute 271.12 4012.89
editCommitRoute 271.12 4012.89
setEditMode -create_crossover_vias 1
editAddRoute 267.05 4010.85
editAddRoute 273.663 4063.25
editCommitRoute 273.663 4063.25
setEditMode -create_crossover_vias 0

setEditMode -nets VDDPST
editAddRoute 404.757 3606.61
editAddRoute 410.861 3669.17
editAddRoute 416.457 3698.17
editAddRoute 425.613 3783.63
editAddRoute 365.078 3862.48
editAddRoute 359.991 4013.56
editCommitRoute 359.991 4013.56
setEditMode -create_crossover_vias 1
editAddRoute 354.904 4013.56
editAddRoute 362.534 4063.92
editCommitRoute 362.534 4063.92
setEditMode -create_crossover_vias 0

setEditMode -nets VSS
editAddRoute 482.003 3683.32
editAddRoute 488.107 3750.47
editAddRoute 488.616 3767.26
editAddRoute 494.721 3865.44
editAddRoute 468.777 3914.78
editAddRoute 455.55 4013.97
editCommitRoute 455.55 4013.97
setEditMode -create_crossover_vias 1
editAddRoute 450.464 4012.45
editAddRoute 455.042 4063.83
editCommitRoute 455.042 4063.83
setEditMode -create_crossover_vias 0

setEditMode -nets VDDPST
editAddRoute 558.816 3609.87
editAddRoute 563.903 3673.45
editAddRoute 565.429 3688.71
editAddRoute 577.638 3788.93
editAddRoute 536.433 3836.74
editAddRoute 532.872 4014.28
editCommitRoute 532.872 4014.28
setEditMode -create_crossover_vias 1
editAddRoute 528.294 4012.96
editAddRoute 532.364 4063.83
editCommitRoute 532.364 4063.83
setEditMode -create_crossover_vias 0

setEditMode -nets VDD
editAddRoute 637.155 3218.78
editAddRoute 638.681 3252.36
editAddRoute 608.668 3280.33
editAddRoute 601.547 3778.75
editAddRoute 545.59 3847.43
editAddRoute 543.555 3949.68
editAddRoute 581.707 3982.74
editAddRoute 585.777 4015.3
editCommitRoute 585.777 4015.3
setEditMode -create_crossover_vias 1
editAddRoute 583.742 4013.47
editAddRoute 589.846 4063.83
editCommitRoute 589.846 4063.83
setEditMode -create_crossover_vias 0

setEditMode -nets VSS
editAddRoute 638.173 3686.37
editAddRoute 640.207 3774.38
editAddRoute 611.212 3821.18
editAddRoute 606.634 3872.05
editAddRoute 659.029 3933.09
editAddRoute 662.59 4011.94
editCommitRoute 662.59 4011.94
setEditMode -create_crossover_vias 1
editAddRoute 661.064 4011.94
editAddRoute 665.134 4063.32
editCommitRoute 665.134 4063.32
setEditMode -create_crossover_vias 0

setEditMode -nets VDDPST
editAddRoute 716.392 3607.41
editAddRoute 714.596 3664.86
editAddRoute 699.037 3694.19
editAddRoute 693.65 3939.56
editAddRoute 705.021 3957.51
editAddRoute 711.006 4013.17
editCommitRoute 711.006 4013.17
setEditMode -create_crossover_vias 1
editAddRoute 708.014 4010.78
editAddRoute 713.999 4062.85
editCommitRoute 713.999 4062.85
setEditMode -create_crossover_vias 0

setEditMode -nets VDD
editAddRoute 794.792 3219.13
editAddRoute 795.39 3253.24
editAddRoute 761.278 3286.16
editAddRoute 761.278 3836.62
editAddRoute 748.111 3849.19
editAddRoute 755.891 4011.38
editCommitRoute 755.891 4011.38
setEditMode -create_crossover_vias 1
editAddRoute 749.907 4009.58
editAddRoute 754.694 4062.85
editCommitRoute 754.694 4062.85
setEditMode -create_crossover_vias 0

setEditMode -nets VSS
editAddRoute 795.39 3688.21
editAddRoute 794.792 3742.67
editAddRoute 820.525 3783.36
editAddRoute 839.078 4013.17
editCommitRoute 839.078 4013.17
setEditMode -create_crossover_vias 1
editAddRoute 837.283 4013.17
editAddRoute 840.874 4062.85
editCommitRoute 840.874 4062.85
setEditMode -create_crossover_vias 0

setEditMode -nets VDDPST
editAddRoute 871.994 3608.61
editAddRoute 871.994 3669.65
editAddRoute 858.827 3688.8
editAddRoute 857.63 3949.74
editAddRoute 891.743 3980.26
editAddRoute 898.924 4012.57
editCommitRoute 898.924 4012.57
setEditMode -create_crossover_vias 1
editAddRoute 894.736 4011.38
editAddRoute 900.121 4063.44
editCommitRoute 900.121 4063.44
setEditMode -create_crossover_vias 0

setEditMode -nets VDD
editAddRoute 951.529 3217.33
editAddRoute 950.931 3246.06
editAddRoute 919.212 3278.97
editAddRoute 920.409 3866.79
editAddRoute 969.484 3898.51
editAddRoute 977.264 4014.01
editCommitRoute 977.264 4014.01
setEditMode -create_crossover_vias 1
editAddRoute 972.476 4011.62
editAddRoute 978.461 4063.08
editCommitRoute 978.461 4063.08
setEditMode -create_crossover_vias 0

setEditMode -nets VSS
editAddRoute 949.734 3687.01
editAddRoute 955.12 3755.83
editAddRoute 1008.98 3809.69
editAddRoute 1011.97 3818.07
editAddRoute 1017.36 4012.57
editCommitRoute 1017.36 4012.57
setEditMode -create_crossover_vias 1
editAddRoute 1014.37 4010.78
editAddRoute 1021.55 4064.04
editCommitRoute 1021.55 4064.04
setEditMode -create_crossover_vias 0

setEditMode -nets VDDPST
editAddRoute 1027.54 3610.4
editAddRoute 1032.92 3670.85
editAddRoute 1053.27 3705.56
editAddRoute 1067.03 4013.77
editCommitRoute 1067.03 4013.77
setEditMode -create_crossover_vias 1
editAddRoute 1065.24 4012.57
editAddRoute 1067.03 4062.85
editCommitRoute 1067.03 4062.85
setEditMode -create_crossover_vias 0

setEditMode -nets VDD
editAddRoute 1105.93 3219.73
editAddRoute 1113.12 3244.86
editAddRoute 1074.81 3277.18
editAddRoute 1086.18 3728.9
editAddRoute 1138.85 3794.73
editAddRoute 1144.83 4014.37
editCommitRoute 1144.83 4014.37
setEditMode -create_crossover_vias 1
editAddRoute 1141.84 4013.77
editAddRoute 1146.03 4063.44
editCommitRoute 1146.03 4063.44
setEditMode -create_crossover_vias 0

setEditMode -nets VSS
editAddRoute 1106.53 3687.61
editAddRoute 1111.32 3723.51
editAddRoute 1155.01 3780.37
editAddRoute 1165.78 3937.17
editAddRoute 1206.48 3975.47
editAddRoute 1214.26 4011.98
editCommitRoute 1214.26 4011.98
setEditMode -create_crossover_vias 1
editAddRoute 1209.47 4011.38
editAddRoute 1211.26 4062.85
editCommitRoute 1211.26 4062.85
setEditMode -create_crossover_vias 0

setEditMode -nets VDDPST
editAddRoute 1184.27 3607.41
editAddRoute 1190.26 3674.44
editAddRoute 1221.38 3716.33
editAddRoute 1245.91 3889.89
editAddRoute 1284.22 3949.74
editAddRoute 1290.2 4011.38
editCommitRoute 1290.2 4011.38
setEditMode -create_crossover_vias 1
editAddRoute 1287.21 4011.38
editAddRoute 1292.6 4062.85
editCommitRoute 1292.6 4062.85
setEditMode -create_crossover_vias 0

setEditMode -nets VDD
editAddRoute 1262.67 3216.73
editAddRoute 1263.27 3250.25
editAddRoute 1238.13 3281.37
editAddRoute 1236.34 3684.38
editAddRoute 1307.56 3778.57
editAddRoute 1332.69 4013.17
editCommitRoute 1332.69 4013.17
setEditMode -create_crossover_vias 1
editAddRoute 1326.71 4013.17
editAddRoute 1330.9 4062.25
editCommitRoute 1330.9 4062.25
setEditMode -create_crossover_vias 0

setEditMode -nets VSS
editAddRoute 1265.48 3686.71
editAddRoute 1324.95 3697.12
editAddRoute 1345.27 3716.94
editAddRoute 1357.66 3947.4
editAddRoute 1353.69 3957.8
editAddRoute 1357.66 4015.29
editCommitRoute 1357.66 4015.29
setEditMode -create_crossover_vias 1
editAddRoute 1351.22 4013.81
editAddRoute 1357.66 4063.86
editCommitRoute 1357.66 4063.86
setEditMode -create_crossover_vias 0

setEditMode -nets VDDPST
editAddRoute 1340.86 3612.75
editAddRoute 1339.07 3648.66
editAddRoute 1361.21 3680.98
editAddRoute 1378.57 4012.54
editCommitRoute 1378.57 4012.54
setEditMode -create_crossover_vias 1
editAddRoute 1373.78 4010.74
editAddRoute 1378.57 4063.41
editCommitRoute 1378.57 4063.41
setEditMode -create_crossover_vias 0

setEditMode -nets VSS
editAddRoute 1418.67 3687.56
editAddRoute 1423.45 3773.74
editAddRoute 1450.39 3807.86
editAddRoute 1461.16 4014.33
editCommitRoute 1461.16 4014.33
setEditMode -create_crossover_vias 1
editAddRoute 1453.98 4013.14
editAddRoute 1460.56 4062.81
editCommitRoute 1460.56 4062.81
setEditMode -create_crossover_vias 0

setEditMode -nets VDDPST
editAddRoute 1495.75 3607.78
editAddRoute 1498.8 3661.2
editAddRoute 1477.94 3682.05
editAddRoute 1470.31 3941.52
editAddRoute 1504.39 3985.27
editAddRoute 1523.22 4013.25
editCommitRoute 1523.22 4013.25
setEditMode -create_crossover_vias 1
editAddRoute 1519.66 4013.25
editAddRoute 1525.76 4063.62
editCommitRoute 1525.76 4063.62
setEditMode -create_crossover_vias 0

setEditMode -nets VDD
editAddRoute 1577.15 3217.97
editAddRoute 1577.65 3251.55
editAddRoute 1547.13 3283.6
editAddRoute 1547.64 3878.94
editAddRoute 1595.46 3933.88
editAddRoute 1602.58 4011.72
editCommitRoute 1602.58 4011.72
setEditMode -create_crossover_vias 1
editAddRoute 1597.49 4011.72
editAddRoute 1600.04 4062.6
editCommitRoute 1600.04 4062.6
setEditMode -create_crossover_vias 0

setEditMode -nets VSS
editAddRoute 1573.94 3687.59
editAddRoute 1577.53 3776.77
editAddRoute 1611.05 3840.22
editAddRoute 1645.17 4013.19
editCommitRoute 1645.17 4013.19
setEditMode -create_crossover_vias 1
editAddRoute 1639.18 4012.59
editAddRoute 1642.77 4064.06
editCommitRoute 1642.77 4064.06
setEditMode -create_crossover_vias 0

setEditMode -nets VSS
editAddRoute 1733.53 3686
editAddRoute 1734.53 3784.13
editAddRoute 1744.44 3809.9
editAddRoute 1739.48 3877.8
editAddRoute 1706.28 3923.89
editAddRoute 1711.23 4015.57
editCommitRoute 1711.23 4015.57
setEditMode -create_crossover_vias 1
editAddRoute 1708.26 4014.58
editAddRoute 1715.2 4063.65
editCommitRoute 1715.2 4063.65
setEditMode -create_crossover_vias 0

setEditMode -nets VDDPST
editAddRoute 1651.15 3608.58
editAddRoute 1654.74 3662.45
editAddRoute 1664.32 3695.97
editAddRoute 1684.67 3724.1
editAddRoute 1689.46 4015.58
editCommitRoute 1689.46 4015.58
setEditMode -create_crossover_vias 1
editAddRoute 1688.26 4014.39
editAddRoute 1693.65 4062.87
editCommitRoute 1693.65 4062.87
setEditMode -create_crossover_vias 0

setEditMode -nets VDD
editAddRoute 1730.7 3216.67
editAddRoute 1734.89 3254.97
editAddRoute 1774.39 3296.27
editAddRoute 1782.17 4011.99
editCommitRoute 1782.17 4011.99
setEditMode -create_crossover_vias 1
editAddRoute 1777.98 4011.39
editAddRoute 1782.17 4061.67
editCommitRoute 1782.17 4061.67
setEditMode -create_crossover_vias 0

setEditMode -nets VDDPST
editAddRoute 1809.59 3608.35
editAddRoute 1800.26 3719.13
editAddRoute 1793.27 3739.54
editAddRoute 1794.43 3853.24
editAddRoute 1827.67 3885.89
editAddRoute 1837.58 4013.58
editCommitRoute 1837.58 4013.58
setEditMode -create_crossover_vias 1
editAddRoute 1827.57 4011.85
editAddRoute 1832.14 4039.85
editCommitRoute 1832.14 4039.85
setEditMode -create_crossover_vias 0

setEditMode -nets VSS
editAddRoute 1885.22 3684.92
editAddRoute 1885.22 3738.34
editAddRoute 1872.5 3763.77
editAddRoute 1870.97 3872.14
editAddRoute 1903.03 3921.49
editAddRoute 1915.74 3932.17
editAddRoute 1920.83 4013.06
editCommitRoute 1920.83 4013.06
setEditMode -create_crossover_vias 1
editAddRoute 1920.83 4013.06
editAddRoute 1921.85 4063.43
editCommitRoute 1921.85 4063.43
setEditMode -create_crossover_vias 0

setEditMode -nets VDD
editAddRoute 1885.89 3216.52
editAddRoute 1892.88 3251.49
editAddRoute 1940.57 3301.08
editAddRoute 1970.45 3840.14
editAddRoute 1951.38 3863.66
editAddRoute 1968.54 4013.08
editCommitRoute 1968.54 4013.08
setEditMode -create_crossover_vias 1
editAddRoute 1967.91 4012.44
editAddRoute 1971.72 4062.67
editCommitRoute 1971.72 4062.67
setEditMode -create_crossover_vias 0

setEditMode -nets VSS
editAddRoute 2042.33 3688.82
editAddRoute 2045.04 3722.33
editAddRoute 2058.55 3738
editAddRoute 2066.11 3860.14
editAddRoute 2040.17 3900.14
editAddRoute 2027.2 4014.71
editCommitRoute 2027.2 4014.71
setEditMode -create_crossover_vias 1
editAddRoute 2021.26 4012.55
editAddRoute 2027.2 4063.89
editCommitRoute 2027.2 4063.89
setEditMode -create_crossover_vias 0

setEditMode -nets VDD
editAddRoute 2040.63 3218.21
editAddRoute 2044.41 3254.96
editAddRoute 2077.92 3281.98
editAddRoute 2086.57 4013.32
editCommitRoute 2086.57 4013.32
setEditMode -create_crossover_vias 1
editAddRoute 2080.62 4012.78
editAddRoute 2085.49 4063.04
editCommitRoute 2085.49 4063.04
setEditMode -create_crossover_vias 0

setEditMode -nets VDDPST
editAddRoute 2120.08 3608.52
editAddRoute 2117.91 3636.63
editAddRoute 2103.86 3662.57
editAddRoute 2104.94 3934.42
editAddRoute 2138.45 3980.36
editAddRoute 2146.56 4014.4
editCommitRoute 2146.56 4014.4
setEditMode -create_crossover_vias 1
editAddRoute 2140.61 4013.86
editAddRoute 2142.77 4063.04
editCommitRoute 2142.77 4063.04
setEditMode -create_crossover_vias 0

setEditMode -nets VSS
editAddRoute 2198.44 3686.89
editAddRoute 2196.82 3725.8
editAddRoute 2175.74 3764.71
editAddRoute 2175.74 3881.45
editAddRoute 2216.82 3929.55
editAddRoute 2223.84 4014.94
editCommitRoute 2223.84 4014.94
setEditMode -create_crossover_vias 1
editAddRoute 2218.98 4014.94
editAddRoute 2223.84 4064.67
editCommitRoute 2223.84 4064.67
setEditMode -create_crossover_vias 0

setEditMode -nets VDD
editAddRoute 2196.43 3216.57
editAddRoute 2199.64 3255.16
editAddRoute 2227.21 3295.58
editAddRoute 2252.02 3817.09
editAddRoute 2257.99 3835.92
editAddRoute 2266.72 4013.25
editCommitRoute 2266.72 4013.25
setEditMode -create_crossover_vias 1
editAddRoute 2259.37 4013.25
editAddRoute 2264.42 4062.87
editCommitRoute 2264.42 4062.87
setEditMode -create_crossover_vias 0

setEditMode -nets VDDPST
editAddRoute 2275.5 3607.99
editAddRoute 2278.2 3652.31
editAddRoute 2289.01 3683.66
editAddRoute 2310.63 4015.51
editCommitRoute 2310.63 4015.51
setEditMode -create_crossover_vias 1
editAddRoute 2307.93 4014.96
editAddRoute 2312.25 4063.61
editCommitRoute 2312.25 4063.61
setEditMode -create_crossover_vias 0

setEditMode -nets VSS
editAddRoute 2353.87 3686.36
editAddRoute 2354.41 3725.27
editAddRoute 2388.46 3761.48
editAddRoute 2398.73 4013.34
editCommitRoute 2398.73 4013.34
setEditMode -create_crossover_vias 1
editAddRoute 2390.62 4011.72
editAddRoute 2395.48 4063.61
editCommitRoute 2395.48 4063.61
setEditMode -create_crossover_vias 0

setEditMode -nets VDD
editAddRoute 2353.33 3216.26
editAddRoute 2354.95 3253.01
editAddRoute 2393.86 3290.84
editAddRoute 2400.89 3709.92
editAddRoute 2399.81 3725.6
editAddRoute 2407.37 3736.41
editAddRoute 2414.4 3937.14
editAddRoute 2443.59 3983.08
editAddRoute 2458.18 4012.8
editCommitRoute 2458.18 4012.8
setEditMode -create_crossover_vias 1
editAddRoute 2456.56 4011.18
editAddRoute 2459.8 4061.45
editCommitRoute 2459.8 4061.45
setEditMode -create_crossover_vias 0

setEditMode -nets VDDPST
editAddRoute 2432.72 3607.99
editAddRoute 2437.05 3644.74
editAddRoute 2476.5 3689.6
editAddRoute 2485.15 3869.58
editAddRoute 2533.79 3922.54
editAddRoute 2537.03 4014.42
editCommitRoute 2537.03 4014.42
setEditMode -create_crossover_vias 1
editAddRoute 2536.49 4012.8
editAddRoute 2540.28 4063.07
editCommitRoute 2540.28 4063.07
setEditMode -create_crossover_vias 0

setEditMode -nets VSS
editAddRoute 2510.01 3687.98
editAddRoute 2513.79 3753.38
editAddRoute 2570 3809.05
editAddRoute 2577.03 4012.8
editCommitRoute 2577.03 4012.8
setEditMode -create_crossover_vias 1
editAddRoute 2572.7 4012.26
editAddRoute 2577.03 4064.15
editCommitRoute 2577.03 4064.15
setEditMode -create_crossover_vias 0

setEditMode -nets VDD
editAddRoute 2511.09 3217.88
editAddRoute 2512.17 3252.47
editAddRoute 2547.3 3300.03
editAddRoute 2574.33 3690.14
editAddRoute 2617.56 3743.65
editAddRoute 2626.21 4012.26
editCommitRoute 2626.21 4012.26
setEditMode -create_crossover_vias 1
editAddRoute 2620.27 4012.26
editAddRoute 2623.51 4061.99
editCommitRoute 2623.51 4061.99
setEditMode -create_crossover_vias 0

setEditMode -nets VDDPST
editAddRoute 2590.89 3608.19
editAddRoute 2596.24 3689.1
editAddRoute 2686.26 3787.69
editAddRoute 2685.19 3868.06
editAddRoute 2647.15 3912
editAddRoute 2649.29 4014.88
editCommitRoute 2649.29 4014.88
setEditMode -create_crossover_vias 1
editAddRoute 2645.54 4013.81
editAddRoute 2650.36 4061.49
editCommitRoute 2650.36 4061.49
setEditMode -create_crossover_vias 0

setEditMode -nets VSS
editAddRoute 2666.2 3685.28
editAddRoute 2665.66 3721.49
editAddRoute 2692.69 3759.32
editAddRoute 2707.28 4011.18
editCommitRoute 2707.28 4011.18
setEditMode -create_crossover_vias 1
editAddRoute 2705.12 4009.02
editAddRoute 2708.9 4063.61
editCommitRoute 2708.9 4063.61
setEditMode -create_crossover_vias 0

setEditMode -nets VDDPST
editAddRoute 2743.49 3609.07
editAddRoute 2745.11 3655.01
editAddRoute 2733.22 3672.85
editAddRoute 2732.68 3955.51
editAddRoute 2762.41 3987.94
editAddRoute 2770.52 4014.42
editCommitRoute 2770.52 4014.42
setEditMode -create_crossover_vias 1
editAddRoute 2764.57 4013.88
editAddRoute 2768.35 4063.61
editCommitRoute 2768.35 4063.61
setEditMode -create_crossover_vias 0

setEditMode -nets VDD
editAddRoute 2821.81 3216.26
editAddRoute 2821.81 3251.39
editAddRoute 2792.08 3275.71
editAddRoute 2788.84 3884.17
editAddRoute 2830.99 3934.98
editAddRoute 2849.37 4012.8
editCommitRoute 2849.37 4012.8
setEditMode -create_crossover_vias 1
editAddRoute 2845.59 4012.8
editAddRoute 2849.91 4061.99
editCommitRoute 2849.91 4061.99
setEditMode -create_crossover_vias 0

setEditMode -nets VSS
editAddRoute 2823.92 3688.91
editAddRoute 2827.89 3744.5
editAddRoute 2882.35 3793.85
editAddRoute 2891.99 4013.39
editCommitRoute 2891.99 4013.39
setEditMode -create_crossover_vias 1
editAddRoute 2885.18 4013.39
editAddRoute 2891.42 4063.31
editCommitRoute 2891.42 4063.31
setEditMode -create_crossover_vias 0

setEditMode -nets VDDPST
editAddRoute 2898.25 3608.51
editAddRoute 2900.46 3653.71
editAddRoute 2928.39 3687.16
editAddRoute 2938.31 4013.82
editCommitRoute 2938.31 4013.82
setEditMode -create_crossover_vias 1
editAddRoute 2932.43 4013.45
editAddRoute 2935.74 4062.7
editCommitRoute 2935.74 4062.7
setEditMode -create_crossover_vias 0

setEditMode -nets VSS
editAddRoute 2977.65 3686.07
editAddRoute 2976.51 3747.34
editAddRoute 2988.43 3773.43
editAddRoute 3000.34 3944.18
editAddRoute 3016.22 3968.01
editAddRoute 3029.27 4014.52
editCommitRoute 3029.27 4014.52
setEditMode -create_crossover_vias 1
editAddRoute 3029.27 4009.42
editAddRoute 3033.81 4063.31
editCommitRoute 3033.81 4063.31
setEditMode -create_crossover_vias 0

setEditMode -nets VDD
editAddRoute 2978.22 3218.75
editAddRoute 2977.65 3260.73
editAddRoute 3000.34 3304.41
editAddRoute 3032.11 3940.21
editAddRoute 3071.25 3971.98
editAddRoute 3078.06 4014.52
editCommitRoute 3078.06 4014.52
setEditMode -create_crossover_vias 1
editAddRoute 3074.09 4014.52
editAddRoute 3078.06 4061.04
editCommitRoute 3078.06 4061.04
setEditMode -create_crossover_vias 0

setEditMode -nets VDDPST
editAddRoute 3054.92 3607.87
editAddRoute 3060.03 3688.99
editAddRoute 3105.98 3734.94
editAddRoute 3115.62 3887.54
editAddRoute 3148.52 3937.46
editAddRoute 3160.43 4012.9
editCommitRoute 3160.43 4012.9
setEditMode -create_crossover_vias 1
editAddRoute 3158.17 4012.9
editAddRoute 3162.7 4062.26
editCommitRoute 3162.7 4062.26
setEditMode -create_crossover_vias 0

setEditMode -nets VSS
uiSetTool addWire
editAddRoute 3132.65 3682.35
editAddRoute 3136.81 3795.2
editAddRoute 3151.74 3810.47
editAddRoute 3156.61 3855.61
editAddRoute 3171.53 3878.18
editAddRoute 3181.26 4014.98
editCommitRoute 3181.26 4014.98
editAddRoute 3174.66 4012.9
editAddRoute 3179.52 4063.59
editCommitRoute 3179.52 4063.59

setEditMode -nets VDD
editAddRoute 3133.77 3220.87
editAddRoute 3135.47 3255.48
editAddRoute 3168.38 3294.05
editAddRoute 3185.96 3856.34
editAddRoute 3195.61 3877.33
editAddRoute 3202.41 4014.61
editCommitRoute 3202.41 4014.61
setEditMode -create_crossover_vias 1
editAddRoute 3197.87 4014.61
editAddRoute 3205.82 4062.26
editCommitRoute 3205.82 4062.26
setEditMode -create_crossover_vias 0

setEditMode -nets VDDPST
editAddRoute 3212.28 3610.71
editAddRoute 3228.17 3677.64
editAddRoute 3217.39 3705.44
editAddRoute 3296.81 3803.01
editAddRoute 3307.59 3860.31
editAddRoute 3280.92 3898.88
editAddRoute 3274.12 4013.47
editCommitRoute 3274.12 4013.47
setEditMode -create_crossover_vias 1
editAddRoute 3271.28 4010.64
editAddRoute 3275.82 4063.39
editCommitRoute 3275.82 4063.39
setEditMode -create_crossover_vias 0

setEditMode -nets VSS
editAddRoute 3291.7 3688.42
editAddRoute 3295.11 3726.43
editAddRoute 3313.83 3757.63
editAddRoute 3328.01 4014.61
editCommitRoute 3328.01 4014.61
setEditMode -create_crossover_vias 1
editAddRoute 3322.34 4012.9
editAddRoute 3326.87 4063.39
editCommitRoute 3326.87 4063.39
setEditMode -create_crossover_vias 0

setEditMode -nets VDD
editAddRoute 3290.57 3216
editAddRoute 3290 3255.71
editAddRoute 3316.09 3296.55
editAddRoute 3345.59 3733.24
editAddRoute 3337.65 3770.68
editAddRoute 3385.87 3824
editAddRoute 3392.11 4012.9
editCommitRoute 3392.11 4012.9
setEditMode -create_crossover_vias 1
editAddRoute 3388.71 4012.9
editAddRoute 3391.54 4037.3
editCommitRoute 3391.54 4037.3
setEditMode -create_crossover_vias 0

setEditMode -nets VDDPST
editAddRoute 3367.15 3607.87
editAddRoute 3367.72 3682.18
editAddRoute 3396.08 3740.61
editAddRoute 3418.2 3893.21
editAddRoute 3473.8 3944.26
editAddRoute 3481.17 4014.04
editCommitRoute 3481.17 4014.04
setEditMode -create_crossover_vias 1
editAddRoute 3477.77 4012.9
editAddRoute 3482.87 4062.26
editCommitRoute 3482.87 4062.26
setEditMode -create_crossover_vias 0

setEditMode -nets VSS
editAddRoute 3445.66 3686.15
editAddRoute 3457.01 3767.27
editAddRoute 3593.15 3917.6
editAddRoute 3601.09 3949.94
editAddRoute 3636.26 3993.05
editAddRoute 3643.64 4012.34
editCommitRoute 3643.64 4012.34
setEditMode -create_crossover_vias 1
editAddRoute 3640.24 4012.34
editAddRoute 3644.77 4062.82
editCommitRoute 3644.77 4062.82
setEditMode -create_crossover_vias 0

setEditMode -nets VSS
editAddRoute 3680.51 3923.84
editAddRoute 3680.51 3964.69
editAddRoute 3703.2 3989.65
editAddRoute 3710.58 4015.17
editCommitRoute 3710.58 4015.17
setEditMode -create_crossover_vias 1
editAddRoute 3705.47 4012.34
editAddRoute 3710.58 4063.39
editCommitRoute 3710.58 4063.39
setEditMode -create_crossover_vias 0

# BOTTOM (left to right)
setEditMode -nets VSS
editAddRoute 324.825 400.835
editAddRoute 333.536 328.706
editAddRoute 370.473 284.104
editAddRoute 371.518 69.876
editCommitRoute 371.518 69.876
setEditMode -create_crossover_vias 1
editAddRoute 370.821 75.451
editAddRoute 371.17 21.7895
editCommitRoute 371.17 21.7895
setEditMode -create_crossover_vias 0

setEditMode -nets VDDPST
editAddRoute 406.449 481.765
editAddRoute 389.883 481.329
editAddRoute 369.829 455.608
editAddRoute 365.034 317.41
editAddRoute 375.06 300.408
editAddRoute 389.011 70.311
editCommitRoute 389.011 70.311
setEditMode -create_crossover_vias 1
editAddRoute 384.216 74.6705
editAddRoute 385.524 22.7915
editCommitRoute 385.524 22.7915
setEditMode -create_crossover_vias 0

setEditMode -nets VDDPST
editAddRoute 404.606 482.159
editAddRoute 405.74 393.096
editAddRoute 423.894 364.165
editAddRoute 438.642 360.194
editAddRoute 442.046 74.2865
editCommitRoute 442.046 74.2865
setEditMode -create_crossover_vias 1
editAddRoute 441.479 84.4975
editAddRoute 444.882 22.0975
editCommitRoute 444.882 22.0975
setEditMode -create_crossover_vias 0

setEditMode -nets VSS
editAddRoute 482.409 404.886
editAddRoute 485.303 317.11
editAddRoute 460.224 294.925
editAddRoute 464.082 167.601
editAddRoute 504.594 123.713
editAddRoute 508.453 70.6615
editCommitRoute 508.453 70.6615
setEditMode -create_crossover_vias 1
editAddRoute 506.041 76.449
editAddRoute 507.488 20.504
editCommitRoute 507.488 20.504

setEditMode -nets VDDPST
editAddRoute 564.01 486.13
editAddRoute 560.607 390.26
editAddRoute 539.051 352.252
editAddRoute 527.705 237.095
editAddRoute 532.811 216.673
editAddRoute 544.723 143.494
editAddRoute 545.857 136.12
editAddRoute 552.665 74.2865
editCommitRoute 552.665 74.2865
setEditMode -create_crossover_vias 1
editAddRoute 551.53 82.2285
editAddRoute 553.799 24.3665
editCommitRoute 553.799 24.3665
setEditMode -create_crossover_vias 0

setEditMode -nets VDD
editAddRoute 637.095 873.218
editAddRoute 643.365 820.647
editAddRoute 615.874 788.816
editAddRoute 588.383 252.208
editAddRoute 598.029 245.456
editAddRoute 595.617 242.079
editAddRoute 599.476 70.381
editCommitRoute 599.476 70.381
setEditMode -create_crossover_vias 1
editAddRoute 596.582 76.1685
editAddRoute 598.994 22.633
editCommitRoute 598.994 22.633
setEditMode -create_crossover_vias 0

setEditMode -nets VSS
editAddRoute 638.135 404.312
editAddRoute 644.376 320.334
editAddRoute 668.775 286.289
editAddRoute 681.259 70.103
editCommitRoute 681.259 70.103
setEditMode -create_crossover_vias 1
editAddRoute 669.677 75.3725
editAddRoute 670.105 20.8025
editCommitRoute 670.105 20.8025
setEditMode -create_crossover_vias 0

setEditMode -nets VDDPST
editAddRoute 715.473 483.86
editAddRoute 719.444 390.827
editAddRoute 743.837 356.223
editAddRoute 760.288 73.7195
editCommitRoute 760.288 73.7195
setEditMode -create_crossover_vias 1
editAddRoute 752.913 84.4975
editAddRoute 755.183 24.3665
editCommitRoute 755.183 24.3665
setEditMode -create_crossover_vias 0

setEditMode -nets VDD
editAddRoute 794.892 875.168
editAddRoute 792.623 819.574
editAddRoute 774.47 784.971
editAddRoute 760.288 394.231
editAddRoute 767.663 380.616
editAddRoute 775.038 163.349
editAddRoute 811.343 121.938
editAddRoute 817.583 74.2865
editCommitRoute 817.583 74.2865
setEditMode -create_crossover_vias 1
editAddRoute 815.881 85.065
editAddRoute 815.314 25.501
editCommitRoute 815.314 25.501
setEditMode -create_crossover_vias 0

setEditMode -nets VSS
editAddRoute 795.38 405.19
editAddRoute 800.487 341.639
editAddRoute 855.527 285.465
editAddRoute 864.038 70.4135
editCommitRoute 864.038 70.4135
setEditMode -create_crossover_vias 1
editAddRoute 854.019 74.54
editAddRoute 857.014 21.2535
editCommitRoute 857.014 21.2535
setEditMode -create_crossover_vias 0

setEditMode -nets VDDPST
editAddRoute 876.126 484.428
editAddRoute 876.126 369.271
editAddRoute 899.952 332.397
editAddRoute 910.163 71.4505
editCommitRoute 910.163 71.4505
setEditMode -create_crossover_vias 1
editAddRoute 910.163 81.094
editAddRoute 910.163 23.232
editCommitRoute 910.163 23.232
setEditMode -create_crossover_vias 0

setEditMode -nets VSS
editAddRoute 953.072 405.553
editAddRoute 955.234 293.993
editAddRoute 969.071 272.805
editAddRoute 963.018 169.029
editAddRoute 928.425 124.923
editAddRoute 933.614 69.4025
editCommitRoute 933.614 69.4025
setEditMode -create_crossover_vias 1
editAddRoute 927.56 75.456
editAddRoute 929.722 20.973
editCommitRoute 929.722 20.973
setEditMode -create_crossover_vias 0

setEditMode -nets VDD
editAddRoute 953.959 875.548
editAddRoute 955.53 814.29
editAddRoute 977.52 785.231
editAddRoute 985.806 777.677
editAddRoute 992.722 70.25
editCommitRoute 992.722 70.25
setEditMode -create_crossover_vias 1
editAddRoute 985.42 74.53
editAddRoute 988.442 23.169
editCommitRoute 988.442 23.169
setEditMode -create_crossover_vias 0

setEditMode -nets VDDPST
editAddRoute 1032.13 484.428
editAddRoute 1032.13 373.808
editAddRoute 1057.09 340.339
editAddRoute 1065.6 73.152
editCommitRoute 1065.6 73.152
setEditMode -create_crossover_vias 1
editAddRoute 1063.33 82.2285
editAddRoute 1065.03 22.0975
editCommitRoute 1065.03 22.0975
setEditMode -create_crossover_vias 0

setEditMode -nets VSS
editAddRoute 1107.39 402.861
editAddRoute 1107.39 346.118
editAddRoute 1089.24 316.613
editAddRoute 1093.21 182.132
editAddRoute 1124.98 133.901
editAddRoute 1133.5 70.349
editCommitRoute 1133.5 70.349
setEditMode -create_crossover_vias 1
editAddRoute 1125.02 73.9285
editAddRoute 1127.12 20.9605
editCommitRoute 1127.12 20.9605
setEditMode -create_crossover_vias 0

setEditMode -nets VDD
editAddRoute 1103.24 871.376
editAddRoute 1112.13 822.503
editAddRoute 1145.01 780.442
editAddRoute 1147.97 223.464
editAddRoute 1158.93 204.211
editAddRoute 1170.18 71.098
editCommitRoute 1170.18 71.098
setEditMode -create_crossover_vias 1
editAddRoute 1165.74 74.6525
editAddRoute 1167.81 22.817
editCommitRoute 1167.81 22.817
setEditMode -create_crossover_vias 0

setEditMode -nets VDDPST
editAddRoute 1185.86 483.86
editAddRoute 1190.96 383.452
editAddRoute 1205.71 352.82
editAddRoute 1211.95 117.967
editAddRoute 1216.49 112.862
editAddRoute 1222.73 73.7195
editCommitRoute 1222.73 73.7195
setEditMode -create_crossover_vias 1
editAddRoute 1221.03 83.9305
editAddRoute 1222.73 22.6645
editCommitRoute 1222.73 22.6645
setEditMode -create_crossover_vias 0

setEditMode -nets VSS
editAddRoute 1264.55 404.942
editAddRoute 1264.92 291.371
editAddRoute 1278.89 274.096
editAddRoute 1265.29 155.012
editAddRoute 1240.66 116.787
editAddRoute 1242.87 69.7405
editCommitRoute 1242.87 69.7405
setEditMode -create_crossover_vias 1
editAddRoute 1241.4 74.372
editAddRoute 1241.4 22.1805
editCommitRoute 1241.4 22.1805
setEditMode -create_crossover_vias 0

setEditMode -nets VDD
editAddRoute 1262.77 878.938
editAddRoute 1267.31 827.301
editAddRoute 1296.82 787.581
editAddRoute 1306.46 70.5705
editCommitRoute 1306.46 70.5705
setEditMode -create_crossover_vias 1
editAddRoute 1299.75 76.7365
editAddRoute 1300.64 22.827
editCommitRoute 1300.64 22.827
setEditMode -create_crossover_vias 0

setEditMode -nets VDDPST
editAddRoute 1341.29 484.995
editAddRoute 1342.99 389.125
editAddRoute 1364.55 355.089
editAddRoute 1378.73 349.416
editAddRoute 1384.41 72.585
editCommitRoute 1384.41 72.585
setEditMode -create_crossover_vias 1
editAddRoute 1381.57 82.2285
editAddRoute 1383.84 23.799
editCommitRoute 1383.84 23.799
setEditMode -create_crossover_vias 0

setEditMode -nets VSS
editAddRoute 1415.51 400.725
editAddRoute 1420.84 327.562
editAddRoute 1401.88 304.459
editAddRoute 1404.25 166.012
editAddRoute 1437.13 133.726
editAddRoute 1440.69 72.412
editCommitRoute 1440.69 72.412
setEditMode -create_crossover_vias 1
editAddRoute 1436.84 75.5515
editAddRoute 1438.91 21.9385
editCommitRoute 1438.91 21.9385
setEditMode -create_crossover_vias 0

setEditMode -nets VDD
editAddRoute 1415.21 871.394
editAddRoute 1417.58 824.594
editAddRoute 1458.46 780.756
editAddRoute 1473.27 134.023
editAddRoute 1484.23 112.103
editAddRoute 1486.9 70.931
editCommitRoute 1486.9 70.931
setEditMode -create_crossover_vias 1
editAddRoute 1483.93 75.374
editAddRoute 1484.23 23.4195
editCommitRoute 1484.23 23.4195
setEditMode -create_crossover_vias 0

setEditMode -nets VDDPST
editAddRoute 1497.29 483.293
editAddRoute 1500.13 396.5
editAddRoute 1522.25 364.732
editAddRoute 1532.46 72.0175
editCommitRoute 1532.46 72.0175
setEditMode -create_crossover_vias 1
editAddRoute 1529.63 82.796
editAddRoute 1534.73 23.232
editCommitRoute 1534.73 23.232
setEditMode -create_crossover_vias 0

setEditMode -nets VSS
editAddRoute 1571.91 402.206
editAddRoute 1572.2 311.567
editAddRoute 1592.34 286.094
editAddRoute 1606.27 276.023
editAddRoute 1611.3 71.523
editCommitRoute 1611.3 71.523
setEditMode -create_crossover_vias 1
editAddRoute 1607.45 74.367
editAddRoute 1609.23 21.05
editCommitRoute 1609.23 21.05
setEditMode -create_crossover_vias 0

setEditMode -nets VDD
editAddRoute 1570.84 872.402
editAddRoute 1575.88 822.936
editAddRoute 1612.6 778.208
editAddRoute 1619.71 346.342
editAddRoute 1628.01 332.421
editAddRoute 1633.04 134.911
editAddRoute 1665.33 105.883
editAddRoute 1667.99 71.227
editCommitRoute 1667.99 71.227
setEditMode -create_crossover_vias 1
editAddRoute 1664.74 75.5515
editAddRoute 1667.4 23.1235
editCommitRoute 1667.4 23.1235
setEditMode -create_crossover_vias 0

setEditMode -nets VDDPST
editAddRoute 1652.84 483.293
editAddRoute 1658.51 398.769
editAddRoute 1690.28 352.252
editAddRoute 1689.71 207.03
editAddRoute 1732.83 152.571
editAddRoute 1753.82 72.0175
editCommitRoute 1753.82 72.0175
setEditMode -create_crossover_vias 1
editAddRoute 1753.82 86.767
editAddRoute 1755.52 21.53
editCommitRoute 1755.52 21.53
setEditMode -create_crossover_vias 0

setEditMode -nets VSS
editAddRoute 1727.83 402.798
editAddRoute 1732.86 347.704
editAddRoute 1777.89 287.279
editAddRoute 1794.77 70.516
editCommitRoute 1794.77 70.516
setEditMode -create_crossover_vias 1
editAddRoute 1788.85 75.2555
editAddRoute 1795.07 21.05
editCommitRoute 1795.07 21.05
setEditMode -create_crossover_vias 0

setEditMode -nets VDD
editAddRoute 1727.95 871.394
editAddRoute 1732.98 821.336
editAddRoute 1758.16 781.941
editAddRoute 1775.34 405.286
editAddRoute 1827.18 341.188
editAddRoute 1830.14 146.345
editAddRoute 1839.32 138.94
editAddRoute 1843.76 70.516
editCommitRoute 1843.76 70.516
setEditMode -create_crossover_vias 1
editAddRoute 1839.02 75.5515
editAddRoute 1842.28 22.531
editCommitRoute 1842.28 22.531
setEditMode -create_crossover_vias 0

setEditMode -nets VDDPST
editAddRoute 1808.97 483.463
editAddRoute 1816.35 399.506
editAddRoute 1914.48 279.81
editAddRoute 1926.96 73.8885
editCommitRoute 1926.96 73.8885
setEditMode -create_crossover_vias 1
editAddRoute 1928.1 85.234
editAddRoute 1929.8 23.4005
editCommitRoute 1929.8 23.4005
setEditMode -create_crossover_vias 0

setEditMode -nets VDD
editAddRoute 1884.05 868.847
editAddRoute 1886.42 822.047
editAddRoute 1848.8 788.872
editAddRoute 1849.39 379.635
editAddRoute 1940.03 270.692
editAddRoute 1951.58 159.377
editAddRoute 1950.1 146.048
editAddRoute 1942.1 70.516
editCommitRoute 1942.1 70.516
setEditMode -create_crossover_vias 1
editAddRoute 1944.18 74.663
editAddRoute 1945.07 23.716
editCommitRoute 1945.07 23.716
setEditMode -create_crossover_vias 0

setEditMode -nets VSS
editAddRoute 2039.85 402.206
editAddRoute 2040.44 352.147
editAddRoute 2004.01 300.904
editAddRoute 1991.57 71.4045
editCommitRoute 1991.57 71.4045
setEditMode -create_crossover_vias 1
editAddRoute 1988.61 75.5515
editAddRoute 1990.38 21.9385
editCommitRoute 1990.38 21.9385
setEditMode -create_crossover_vias 0

setEditMode -nets VDD
editAddRoute 2042.25 873.389
editAddRoute 2045.35 824.258
editAddRoute 2080.76 785.307
editAddRoute 2076.33 326.221
editAddRoute 2069.69 307.189
editAddRoute 2066.59 70.83
editCommitRoute 2066.59 70.83
setEditMode -create_crossover_vias 1
editAddRoute 2063.05 76.141
editAddRoute 2067.92 22.584
editCommitRoute 2067.92 22.584
setEditMode -create_crossover_vias 0

setEditMode -nets VDDPST
editAddRoute 2121.34 483.388
editAddRoute 2126.24 390.269
editAddRoute 2127.46 366.99
editAddRoute 2139.72 349.837
editAddRoute 2139.72 289.187
editAddRoute 2106.64 240.177
editAddRoute 2108.47 134.193
editAddRoute 2107.25 122.553
editAddRoute 2114.6 71.7055
editCommitRoute 2114.6 71.7055
setEditMode -create_crossover_vias 1
editAddRoute 2105.95 75.0565
editAddRoute 2109.65 20.7595
editCommitRoute 2109.65 20.7595
setEditMode -create_crossover_vias 0

setEditMode -nets VSS
editAddRoute 2200.38 405.428
editAddRoute 2199.86 285.139
editAddRoute 2169.65 238.794
editAddRoute 2160.8 71.639
editCommitRoute 2160.8 71.639
setEditMode -create_crossover_vias 1
editAddRoute 2149.48 75.1455
editAddRoute 2152.19 21.868
editCommitRoute 2152.19 21.868
setEditMode -create_crossover_vias 0

setEditMode -nets VDD
editAddRoute 2195.11 870.909
editAddRoute 2199.45 821.981
editAddRoute 2230.17 792.08
editAddRoute 2234.79 72.2305
editCommitRoute 2234.79 72.2305
setEditMode -create_crossover_vias 1
editAddRoute 2229.36 74.4055
editAddRoute 2233.7 23.302
editCommitRoute 2233.7 23.302
setEditMode -create_crossover_vias 0

setEditMode -nets VDDPST
editAddRoute 2275.79 483.988
editAddRoute 2287.25 398.067
editAddRoute 2302.35 368.385
editAddRoute 2312.77 362.135
editAddRoute 2319.54 71.045
editCommitRoute 2319.54 71.045
setEditMode -create_crossover_vias 1
editAddRoute 2315.37 76.252
editAddRoute 2315.89 22.0955
editCommitRoute 2315.89 22.0955
setEditMode -create_crossover_vias 0

setEditMode -nets VSS
editAddRoute 2353.91 404.836
editAddRoute 2358.59 302.251
editAddRoute 2342.97 280.38
editAddRoute 2350.26 159.57
editAddRoute 2373.69 121.556
editAddRoute 2382.02 72.086
editCommitRoute 2382.02 72.086
setEditMode -create_crossover_vias 1
editAddRoute 2372.95 74.496
editAddRoute 2378.72 21.585
editCommitRoute 2378.72 21.585
setEditMode -create_crossover_vias 0

setEditMode -nets VDD
editAddRoute 2354.04 877.716
editAddRoute 2355.6 824.601
editAddRoute 2389.97 798.043
editAddRoute 2394.13 247.729
editAddRoute 2412.88 222.733
editAddRoute 2418.02 70.6605
editCommitRoute 2418.02 70.6605
setEditMode -create_crossover_vias 1
editAddRoute 2415.14 74.498
editAddRoute 2419.62 23.0105
editCommitRoute 2419.62 23.0105
setEditMode -create_crossover_vias 0

setEditMode -nets VDDPST
editAddRoute 2431.98 483.727
editAddRoute 2438.75 362.916
editAddRoute 2460.62 327.506
editAddRoute 2471.56 71.3035
editCommitRoute 2471.56 71.3035
setEditMode -create_crossover_vias 1
editAddRoute 2468.43 76.511
editAddRoute 2470.51 22.354
editCommitRoute 2470.51 22.354
setEditMode -create_crossover_vias 0

setEditMode -nets VSS
editAddRoute 2510.09 406.658
editAddRoute 2517.38 302.51
editAddRoute 2534.04 269.183
editAddRoute 2552.27 71.3035
editCommitRoute 2552.27 71.3035
setEditMode -create_crossover_vias 1
editAddRoute 2539.3 74.8
editAddRoute 2540.72 20.596
editCommitRoute 2540.72 20.596
setEditMode -create_crossover_vias 0

setEditMode -nets VDD
editAddRoute 2511.05 876.019
editAddRoute 2515.34 828.233
editAddRoute 2546.58 788.412
editAddRoute 2566.18 291.074
editAddRoute 2615.81 213.882
editAddRoute 2633.2 69.729
editCommitRoute 2633.2 69.729
setEditMode -create_crossover_vias 1
editAddRoute 2626.05 74.9965
editAddRoute 2627.18 22.7
editCommitRoute 2627.18 22.7
setEditMode -create_crossover_vias 0

setEditMode -nets VDDPST
editAddRoute 2587.57 483.603
editAddRoute 2594.86 392.995
editAddRoute 2629.75 352.377
editAddRoute 2635.48 235.73
editAddRoute 2676.62 177.928
editAddRoute 2689.11 72.7375
editCommitRoute 2689.11 72.7375
setEditMode -create_crossover_vias 1
editAddRoute 2690.15 77.4245
editAddRoute 2692.24 21.705
editCommitRoute 2692.24 21.705
setEditMode -create_crossover_vias 0

setEditMode -nets VSS
editAddRoute 2666.72 406.013
editAddRoute 2673.49 287.805
editAddRoute 2720.36 225.836
editAddRoute 2732.86 70.655
editCommitRoute 2732.86 70.655
setEditMode -create_crossover_vias 1
editAddRoute 2728.48 74.8725
editAddRoute 2733.79 21.314
editCommitRoute 2733.79 21.314
setEditMode -create_crossover_vias 0

setEditMode -nets VDDPST
editAddRoute 2742.8 483.553
editAddRoute 2744.57 378.649
editAddRoute 2777.76 327.304
editAddRoute 2787.5 229.304
editAddRoute 2784.4 213.37
editAddRoute 2781.31 72.1695
editCommitRoute 2781.31 72.1695
setEditMode -create_crossover_vias 1
editAddRoute 2779.09 77.7465
editAddRoute 2778.65 22.4175
editCommitRoute 2778.65 22.4175
setEditMode -create_crossover_vias 0

setEditMode -nets VDD
editAddRoute 2819.69 870.468
editAddRoute 2820.74 816.472
editAddRoute 2790.08 781.985
editAddRoute 2791.82 368.062
editAddRoute 2851.74 296.647
editAddRoute 2859.4 70.282
editCommitRoute 2859.4 70.282
setEditMode -create_crossover_vias 1
editAddRoute 2858.01 73.766
editAddRoute 2862.19 24.2985
editCommitRoute 2862.19 24.2985
setEditMode -create_crossover_vias 0

setEditMode -nets VSS
editAddRoute 2821.77 406.495
editAddRoute 2825.23 362.824
editAddRoute 2929.87 246.944
editAddRoute 2940.24 70.0965
editCommitRoute 2940.24 70.0965
setEditMode -create_crossover_vias 1
editAddRoute 2935.64 74.4395
editAddRoute 2937.5 20.8005
editCommitRoute 2937.5 20.8005
setEditMode -create_crossover_vias 0

setEditMode -nets VDDPST
editAddRoute 2899.05 485.59
editAddRoute 2906.57 406.358
editAddRoute 2949.06 346.603
editAddRoute 2956.15 186.812
editAddRoute 2986.24 147.86
editAddRoute 2999.97 72.1695
editCommitRoute 2999.97 72.1695
setEditMode -create_crossover_vias 1
editAddRoute 2998.2 76.8615
editAddRoute 2999.52 22.86
editCommitRoute 2999.52 22.86
setEditMode -create_crossover_vias 0

setEditMode -nets VDD
editAddRoute 2976.03 874.596
editAddRoute 2976.47 819.71
editAddRoute 2952.12 774.561
editAddRoute 2945.49 398.233
editAddRoute 3032.68 292.887
editAddRoute 3040.21 290.32
editAddRoute 3041.09 69.8875
editCommitRoute 3041.09 69.8875
setEditMode -create_crossover_vias 1
editAddRoute 3042.42 76.0845
editAddRoute 3044.64 23.8535
editCommitRoute 3044.64 23.8535
setEditMode -create_crossover_vias 0

setEditMode -nets VSS
editAddRoute 2981.09 405.31
editAddRoute 2982.97 368.139
editAddRoute 3064.84 275.916
editAddRoute 3077.08 69.356
editCommitRoute 3077.08 69.356
setEditMode -create_crossover_vias 1
editAddRoute 3070.02 74.5315
editAddRoute 3071.43 20.892
editCommitRoute 3071.43 20.892
setEditMode -create_crossover_vias 0

setEditMode -nets VDDPST
editAddRoute 3054.01 481.324
editAddRoute 3054.32 374.17
editAddRoute 3074.31 341.368
editAddRoute 3091.81 70.764
editCommitRoute 3091.81 70.764
setEditMode -create_crossover_vias 1
editAddRoute 3087.12 75.1375
editAddRoute 3089.62 22.029
editCommitRoute 3089.62 22.029
setEditMode -create_crossover_vias 0

setEditMode -nets VDD
editAddRoute 3134.89 872.64
editAddRoute 3136.11 809.538
editAddRoute 3099.97 769.104
editAddRoute 3109.15 383.872
editAddRoute 3132.44 321.382
editAddRoute 3160.62 314.643
editAddRoute 3166.13 310.967
editAddRoute 3174.09 69.585
editCommitRoute 3174.09 69.585
setEditMode -create_crossover_vias 1
editAddRoute 3167 73.7325
editAddRoute 3170.39 22.94
editCommitRoute 3170.39 22.94
setEditMode -create_crossover_vias 0

setEditMode -nets VSS
editAddRoute 3133.98 404.079
editAddRoute 3133.98 372.656
editAddRoute 3177.42 317.664
editAddRoute 3188.97 230.788
editAddRoute 3231.02 169.328
editAddRoute 3254.12 71.3615
editCommitRoute 3254.12 71.3615
setEditMode -create_crossover_vias 1
editAddRoute 3248.78 74.349
editAddRoute 3250.48 20.4285
editCommitRoute 3250.48 20.4285
setEditMode -create_crossover_vias 0

setEditMode -nets VDDPST
editAddRoute 3213.01 482.971
editAddRoute 3216.82 387.288
editAddRoute 3250.53 345.426
editAddRoute 3258.14 212.231
editAddRoute 3298.37 155.69
editAddRoute 3313.05 71.4235
editCommitRoute 3313.05 71.4235
setEditMode -create_crossover_vias 1
editAddRoute 3309.39 76.757
editAddRoute 3310.17 22.9445
editCommitRoute 3310.17 22.9445
setEditMode -create_crossover_vias 0

setEditMode -nets VDD
editAddRoute 3287.61 870.657
editAddRoute 3287.41 818.986
editAddRoute 3327.59 778.389
editAddRoute 3338.05 221.457
editAddRoute 3341.74 213.256
editAddRoute 3346.25 122.382
editAddRoute 3352.4 111.924
editAddRoute 3355.07 71.7365
editCommitRoute 3355.07 71.7365
setEditMode -create_crossover_vias 1
editAddRoute 3350.97 74.197
editAddRoute 3355.68 22.3215
editCommitRoute 3355.68 22.3215
setEditMode -create_crossover_vias 0

setEditMode -nets VDDPST
editAddRoute 3368.83 485.337
editAddRoute 3382.16 388.06
editAddRoute 3385.12 355.963
editAddRoute 3404.87 72.5255
editCommitRoute 3404.87 72.5255
setEditMode -create_crossover_vias 1
editAddRoute 3397.53 75.772
editAddRoute 3405.11 23.6125
editCommitRoute 3405.11 23.6125
setEditMode -create_crossover_vias 0

setEditMode -nets VSS
editAddRoute 3448.83 407.065
editAddRoute 3452.29 292.505
editAddRoute 3472.54 261.889
editAddRoute 3482.41 71.778
editCommitRoute 3482.41 71.778
setEditMode -create_crossover_vias 1
editAddRoute 3473.09 74.662
editAddRoute 3475.28 21.64
editCommitRoute 3475.28 21.64
setEditMode -create_crossover_vias 0

setEditMode -nets VSS
editAddRoute 3605.11 408.065
editAddRoute 3603.37 323.248
editAddRoute 3576.07 290.716
editAddRoute 3573.16 72.2825
editCommitRoute 3573.16 72.2825
setEditMode -create_crossover_vias 1
editAddRoute 3565.83 75.4765
editAddRoute 3565.27 20.537
editCommitRoute 3565.27 20.537
setEditMode -create_crossover_vias 0

# LEFT (top to bottom)
# Draw long VDD wire
setEditMode -nets VDD
editAddRoute 638.565 3217.44
editAddRoute 606.538 3215.4
editAddRoute 585.413 3242.66
editAddRoute 564.97 3254.92
editAddRoute 536.69 3253.9
editAddRoute 518.631 3233.8
editAddRoute 522.039 851.417
editCommitRoute 522.039 851.417

setEditMode -nets VSS
editAddRoute 324.667 3680.5
editAddRoute 325.729 3659.26
editAddRoute 310.062 3646.51
editAddRoute 305.814 3641.2
editAddRoute 69.483 3628.19
editCommitRoute 69.483 3628.19
setEditMode -create_crossover_vias 1
editAddRoute 72.6695 3639.08
editAddRoute 23.5445 3637.48
editCommitRoute 23.5445 3637.48
setEditMode -create_crossover_vias 0

setEditMode -nets VDDPST
editAddRoute 403.209 3603.45
editAddRoute 404.772 3577.84
editAddRoute 391.963 3562.84
editAddRoute 69.565 3555.66
editCommitRoute 69.565 3555.66
setEditMode -create_crossover_vias 1
editAddRoute 73.3135 3562.22
editAddRoute 23.642 3557.53
editCommitRoute 23.642 3557.53
setEditMode -create_crossover_vias 0

setEditMode -nets VSS
uiSetTool addWire
editAddRoute 329.93 3530.62
editAddRoute 115.772 3527.57
editAddRoute 95.4245 3545.37
editAddRoute 69.8595 3544.64
editCommitRoute 69.8595 3544.64
setEditMode -create_crossover_vias 1
editAddRoute 72.5455 3545.02
editAddRoute 23.623 3542.14
editCommitRoute 23.623 3542.14
setEditMode -create_crossover_vias 0

setEditMode -nets VSS
editAddRoute 248.09 3451.57
editAddRoute 135.994 3449
editAddRoute 99.9755 3484.28
editAddRoute 70.205 3488.69
editCommitRoute 70.205 3488.69
setEditMode -create_crossover_vias 1
editAddRoute 74.983 3485.02
editAddRoute 24.6315 3483.18
editCommitRoute 24.6315 3483.18
setEditMode -create_crossover_vias 0

setEditMode -nets VDDPST
editAddRoute 483.311 3373.66
editAddRoute 400.984 3368.88
editAddRoute 362.76 3341.31
editAddRoute 292.195 3334.33
editAddRoute 237.432 3398.28
editAddRoute 70.205 3395.34
editCommitRoute 70.205 3395.34
setEditMode -create_crossover_vias 1
editAddRoute 74.6155 3397.91
editAddRoute 24.2635 3392.77
editCommitRoute 24.2635 3392.77
setEditMode -create_crossover_vias 0

setEditMode -nets VSS
editAddRoute 249.263 3293.73
editAddRoute 249.576 3320.59
editAddRoute 234.893 3340.9
editAddRoute 70.257 3341.21
editCommitRoute 70.257 3341.21
setEditMode -create_crossover_vias 1
editAddRoute 74.318 3340.59
editAddRoute 23.084 3333.71
editCommitRoute 23.084 3333.71
setEditMode -create_crossover_vias 0

setEditMode -nets VSS
editAddRoute 247.998 3291.99
editAddRoute 248.999 3261.28
editAddRoute 230.302 3246.92
editAddRoute 70.3685 3244.92
editCommitRoute 70.3685 3244.92
setEditMode -create_crossover_vias 1
editAddRoute 74.375 3244.25
editAddRoute 23.29 3241.24
editCommitRoute 23.29 3241.24
setEditMode -create_crossover_vias 0

setEditMode -nets VDDPST
editAddRoute 481.387 3214.53
editAddRoute 483.389 3237.24
editAddRoute 473.039 3253.93
editAddRoute 296.077 3249.26
editAddRoute 227.297 3193.16
editAddRoute 69.7005 3184.48
editCommitRoute 69.7005 3184.48
setEditMode -create_crossover_vias 1
editAddRoute 73.707 3184.48
editAddRoute 24.6255 3184.48
editCommitRoute 24.6255 3184.48
setEditMode -create_crossover_vias 0

setEditMode -nets VSS
editAddRoute 248.666 3137.8
editAddRoute 249.333 3105.42
editAddRoute 225.627 3089.06
editAddRoute 69.7005 3083.71
editCommitRoute 69.7005 3083.71
setEditMode -create_crossover_vias 1
editAddRoute 73.707 3083.71
editAddRoute 23.6235 3082.05
editCommitRoute 23.6235 3082.05
setEditMode -create_crossover_vias 0

setEditMode -nets VDD
editAddRoute 517.95 3013.83
editAddRoute 146.565 3019.96
editAddRoute 123.056 3038.02
editAddRoute 70.585 3039.38
editCommitRoute 70.585 3039.38
setEditMode -create_crossover_vias 1
editAddRoute 75.0145 3037.34
editAddRoute 28.336 3035.98
editCommitRoute 28.336 3035.98
setEditMode -create_crossover_vias 0

setEditMode -nets VSS
editAddRoute 251.852 2982.77
editAddRoute 141.591 2979.74
editAddRoute 103.109 3018.66
editAddRoute 69.8145 3018.66
editCommitRoute 69.8145 3018.66
setEditMode -create_crossover_vias 1
editAddRoute 75.003 3019.09
editAddRoute 23.9805 3015.2
editCommitRoute 23.9805 3015.2
setEditMode -create_crossover_vias 0

setEditMode -nets VDDPST
editAddRoute 481.387 2903.82
editAddRoute 481.387 2874.77
editAddRoute 465.026 2866.09
editAddRoute 320.118 2866.75
editAddRoute 263.356 2930.19
editAddRoute 70.0345 2930.53
editCommitRoute 70.0345 2930.53
setEditMode -create_crossover_vias 1
editAddRoute 74.041 2929.86
editAddRoute 22.956 2927.52
editCommitRoute 22.956 2927.52
setEditMode -create_crossover_vias 0

setEditMode -nets VSS
editAddRoute 246.328 2824.68
editAddRoute 246.996 2849.39
editAddRoute 231.971 2867.42
editAddRoute 70.3685 2872.76
editCommitRoute 70.3685 2872.76
setEditMode -create_crossover_vias 1
editAddRoute 74.709 2866.75
editAddRoute 23.6235 2864.75
editCommitRoute 23.6235 2864.75
setEditMode -create_crossover_vias 0

setEditMode -nets VDDPST
editAddRoute 480.385 2745.55
editAddRoute 480.051 2769.59
editAddRoute 466.695 2781.95
editAddRoute 70.0345 2772.93
editCommitRoute 70.0345 2772.93
setEditMode -create_crossover_vias 1
editAddRoute 74.375 2782.95
editAddRoute 23.29 2776.94
editCommitRoute 23.29 2776.94
setEditMode -create_crossover_vias 0

setEditMode -nets VDD
editAddRoute 518.291 2712.36
editAddRoute 70.585 2716.45
editCommitRoute 70.585 2716.45
setEditMode -create_crossover_vias 1
editAddRoute 75.3555 2712.02
editAddRoute 23.9065 2709.98
editCommitRoute 23.9065 2709.98
setEditMode -create_crossover_vias 0

setEditMode -nets VSS
editAddRoute 247.998 2666.82
editAddRoute 247.998 2642.45
editAddRoute 224.625 2628.09
editAddRoute 70.0345 2614.4
editCommitRoute 70.0345 2614.4
setEditMode -create_crossover_vias 1
editAddRoute 74.375 2619.74
editAddRoute 23.6235 2618.41
editCommitRoute 23.6235 2618.41
setEditMode -create_crossover_vias 0

setEditMode -nets VDDPST
editAddRoute 483.056 2588.69
editAddRoute 483.389 2614.4
editAddRoute 468.365 2630.76
editAddRoute 288.398 2632.1
editAddRoute 219.617 2566.32
editAddRoute 70.0345 2556.3
editCommitRoute 70.0345 2556.3
setEditMode -create_crossover_vias 1
editAddRoute 74.709 2561.31
editAddRoute 24.2915 2559.64
editCommitRoute 24.2915 2559.64
setEditMode -create_crossover_vias 0

setEditMode -nets VSS
editAddRoute 246.996 2511.23
editAddRoute 246.996 2484.52
editAddRoute 225.627 2467.15
editAddRoute 69.3665 2459.81
editCommitRoute 69.3665 2459.81
setEditMode -create_crossover_vias 1
editAddRoute 73.707 2462.81
editAddRoute 23.29 2461.48
editCommitRoute 23.29 2461.48
setEditMode -create_crossover_vias 0

setEditMode -nets VDDPST
editAddRoute 481.721 2436.17
editAddRoute 481.721 2458.87
editAddRoute 464.024 2474.23
editAddRoute 295.41 2472.56
editAddRoute 226.629 2411.13
editAddRoute 69.7005 2404.78
editCommitRoute 69.7005 2404.78
setEditMode -create_crossover_vias 1
editAddRoute 74.041 2406.45
editAddRoute 23.9575 2405.45
editCommitRoute 23.9575 2405.45
setEditMode -create_crossover_vias 0

setEditMode -nets VDD
editAddRoute 518.631 2395.63
editAddRoute 303.297 2379.95
editAddRoute 294.438 2387.11
editAddRoute 69.904 2382.68
editCommitRoute 69.904 2382.68
setEditMode -create_crossover_vias 1
editAddRoute 74.333 2385.75
editAddRoute 23.566 2385.41
editCommitRoute 23.566 2385.41
setEditMode -create_crossover_vias 0

setEditMode -nets VSS
editAddRoute 247.663 2355.37
editAddRoute 247.663 2329.99
editAddRoute 223.29 2309.29
editAddRoute 69.7005 2304.28
editCommitRoute 69.7005 2304.28
setEditMode -create_crossover_vias 1
editAddRoute 73.707 2305.62
editAddRoute 23.9575 2303.62
editCommitRoute 23.9575 2303.62
setEditMode -create_crossover_vias 0

setEditMode -nets VDDPST
editAddRoute 481.387 2277.57
editAddRoute 482.722 2248.86
editAddRoute 465.026 2238.17
editAddRoute 70.702 2237.17
editCommitRoute 70.702 2237.17
setEditMode -create_crossover_vias 1
editAddRoute 75.0425 2232.5
editAddRoute 24.6255 2231.83
editCommitRoute 24.6255 2231.83
setEditMode -create_crossover_vias 0

setEditMode -nets VSS
editAddRoute 247.998 2200.38
editAddRoute 249.667 2172.66
editAddRoute 233.306 2151.3
editAddRoute 69.7005 2144.95
editCommitRoute 69.7005 2144.95
setEditMode -create_crossover_vias 1
editAddRoute 73.3735 2150.63
editAddRoute 23.6235 2148.62
editCommitRoute 23.6235 2148.62
setEditMode -create_crossover_vias 0

setEditMode -nets VDDPST
editAddRoute 480.719 2122.25
editAddRoute 480.719 2147.96
editAddRoute 463.356 2160.98
editAddRoute 291.07 2162.98
editAddRoute 211.938 2090.86
editAddRoute 70.702 2089.19
editCommitRoute 70.702 2089.19
setEditMode -create_crossover_vias 1
editAddRoute 75.3765 2086.19
editAddRoute 24.6255 2085.19
editCommitRoute 24.6255 2085.19
setEditMode -create_crossover_vias 0

setEditMode -nets VDDPST
editAddRoute 480.051 1965.32
editAddRoute 480.719 1991.36
editAddRoute 464.692 2004.72
editAddRoute 69.7005 1998.04
editCommitRoute 69.7005 1998.04
setEditMode -create_crossover_vias 1
editAddRoute 73.707 2006.72
editAddRoute 23.6235 2004.38
editCommitRoute 23.6235 2004.38
setEditMode -create_crossover_vias 0

setEditMode -nets VDD
editAddRoute 518.631 1931.63
editAddRoute 441.629 1933
editAddRoute 388.476 1995.35
editAddRoute 69.2225 1995.35
editCommitRoute 69.2225 1995.35
setEditMode -create_crossover_vias 1
editAddRoute 74.333 1995.01
editAddRoute 23.566 1992.62
editCommitRoute 23.566 1992.62
setEditMode -create_crossover_vias 0

setEditMode -nets VSS
editAddRoute 246.996 1889.53
editAddRoute 246.996 1912.23
editAddRoute 228.966 1932.6
editAddRoute 70.0345 1936.94
editCommitRoute 70.0345 1936.94
setEditMode -create_crossover_vias 1
editAddRoute 74.375 1932.26
editAddRoute 23.9575 1930.93
editCommitRoute 23.9575 1930.93
setEditMode -create_crossover_vias 0

setEditMode -nets VSS
editAddRoute 248.332 1886.12
editAddRoute 248.332 1858.08
editAddRoute 226.294 1842.38
editAddRoute 70.702 1839.71
editCommitRoute 70.702 1839.71
setEditMode -create_crossover_vias 1
editAddRoute 74.375 1836.71
editAddRoute 23.29 1836.04
editCommitRoute 23.29 1836.04
setEditMode -create_crossover_vias 0

setEditMode -nets VDDPST
editAddRoute 480.719 1810.66
editAddRoute 479.717 1834.37
editAddRoute 460.017 1859.08
editAddRoute 299.75 1854.74
editAddRoute 220.619 1786.29
editAddRoute 69.7005 1779.28
editCommitRoute 69.7005 1779.28
setEditMode -create_crossover_vias 1
editAddRoute 73.707 1779.61
editAddRoute 23.9575 1779.61
editCommitRoute 23.9575 1779.61
setEditMode -create_crossover_vias 0

setEditMode -nets VDD
editAddRoute 518.291 1764.27
editAddRoute 310.452 1758.14
editAddRoute 305 1759.84
editAddRoute 200.059 1758.82
editAddRoute 138.048 1696.47
editAddRoute 69.563 1693.06
editCommitRoute 69.563 1693.06
setEditMode -create_crossover_vias 1
editAddRoute 74.674 1696.47
editAddRoute 24.588 1695.45
editCommitRoute 24.588 1695.45
setEditMode -create_crossover_vias 0

setEditMode -nets VSS
editAddRoute 246.662 1731.53
editAddRoute 247.663 1700.48
editAddRoute 226.963 1684.45
editAddRoute 69.7005 1683.45
editCommitRoute 69.7005 1683.45
setEditMode -create_crossover_vias 1
editAddRoute 74.709 1679.78
editAddRoute 23.9575 1677.11
editCommitRoute 23.9575 1677.11
setEditMode -create_crossover_vias 0

setEditMode -nets VDDPST
editAddRoute 481.053 1652.73
editAddRoute 481.387 1676.77
editAddRoute 467.363 1691.13
editAddRoute 290.401 1689.13
editAddRoute 221.954 1625.35
editAddRoute 69.3665 1623.02
editCommitRoute 69.3665 1623.02
setEditMode -create_crossover_vias 1
editAddRoute 73.3735 1622.35
editAddRoute 24.2915 1621.01
editCommitRoute 24.2915 1621.01
setEditMode -create_crossover_vias 0

setEditMode -nets VSS
editAddRoute 246.662 1575.87
editAddRoute 249.333 1547.49
editAddRoute 225.293 1526.79
editAddRoute 70.0345 1526.12
editCommitRoute 70.0345 1526.12
setEditMode -create_crossover_vias 1
editAddRoute 74.375 1525.79
editAddRoute 23.29 1525.12
editCommitRoute 23.29 1525.12
setEditMode -create_crossover_vias 0

setEditMode -nets VDD
editAddRoute 517.95 1526.38
editAddRoute 270.928 1524.68
editAddRoute 211.643 1471.87
editAddRoute 69.904 1467.1
editCommitRoute 69.904 1467.1
setEditMode -create_crossover_vias 1
editAddRoute 75.3555 1467.1
editAddRoute 23.566 1466.42
editCommitRoute 23.566 1466.42
setEditMode -create_crossover_vias 0

setEditMode -nets VDDPST
editAddRoute 481.053 1495.4
editAddRoute 481.721 1472.37
editAddRoute 463.69 1455.67
editAddRoute 70.3685 1453.67
editCommitRoute 70.3685 1453.67
setEditMode -create_crossover_vias 1
editAddRoute 74.041 1454.34
editAddRoute 24.2915 1453
editCommitRoute 24.2915 1453
setEditMode -create_crossover_vias 0

setEditMode -nets VSS
editAddRoute 247.998 1421.28
editAddRoute 247.998 1394.24
editAddRoute 247.998 1388.89
editAddRoute 226.294 1372.87
editAddRoute 69.3665 1366.19
editCommitRoute 69.3665 1366.19
setEditMode -create_crossover_vias 1
editAddRoute 73.707 1367.86
editAddRoute 22.956 1366.19
editCommitRoute 22.956 1366.19
setEditMode -create_crossover_vias 0

setEditMode -nets VDDPST
editAddRoute 480.385 1340.81
editAddRoute 480.719 1366.86
editAddRoute 462.688 1381.88
editAddRoute 291.07 1379.21
editAddRoute 218.615 1318.11
editAddRoute 69.3665 1313.43
editCommitRoute 69.3665 1313.43
setEditMode -create_crossover_vias 1
editAddRoute 73.3735 1312.1
editAddRoute 23.9575 1312.1
editCommitRoute 23.9575 1312.1
setEditMode -create_crossover_vias 0

setEditMode -nets VSS
editAddRoute 248.332 1262.95
editAddRoute 250.335 1230.23
editAddRoute 227.964 1214.2
editAddRoute 70.0345 1210.53
editCommitRoute 70.0345 1210.53
setEditMode -create_crossover_vias 1
editAddRoute 74.041 1210.87
editAddRoute 23.29 1208.19
editCommitRoute 23.29 1208.19
setEditMode -create_crossover_vias 0

setEditMode -nets VDDPST
editAddRoute 481.387 1185.49
editAddRoute 483.056 1157.11
editAddRoute 472.038 1147.09
editAddRoute 69.0325 1147.09
editCommitRoute 69.0325 1147.09
setEditMode -create_crossover_vias 1
editAddRoute 73.0395 1146.42
editAddRoute 22.956 1142.75
editCommitRoute 22.956 1142.75
setEditMode -create_crossover_vias 0

setEditMode -nets VDD
editAddRoute 518.291 1129.51
editAddRoute 197.333 1133.6
editAddRoute 143.499 1067.5
editAddRoute 69.904 1068.18
editCommitRoute 69.904 1068.18
setEditMode -create_crossover_vias 1
editAddRoute 75.3555 1067.5
editAddRoute 25.2695 1067.16
editCommitRoute 25.2695 1067.16
setEditMode -create_crossover_vias 0

setEditMode -nets VSS
editAddRoute 247.998 1106.02
editAddRoute 249.333 1074.3
editAddRoute 226.963 1058.61
editAddRoute 69.7005 1043.59
editCommitRoute 69.7005 1043.59
setEditMode -create_crossover_vias 1
editAddRoute 73.707 1053.6
editAddRoute 23.29 1052.93
editCommitRoute 23.29 1052.93
setEditMode -create_crossover_vias 0

setEditMode -nets VDDPST
editAddRoute 480.385 1029.56
editAddRoute 481.721 1055.94
editAddRoute 467.029 1068.96
editAddRoute 278.048 1067.96
editAddRoute 206.262 1001.52
editAddRoute 70.0345 1000.85
editCommitRoute 70.0345 1000.85
setEditMode -create_crossover_vias 1
editAddRoute 74.375 997.51
editAddRoute 23.6235 997.51
editCommitRoute 23.6235 997.51
setEditMode -create_crossover_vias 0

setEditMode -nets VSS
editAddRoute 248.332 945.691
editAddRoute 248.332 919.981
editAddRoute 229.633 905.624
editAddRoute 70.3685 902.284
editCommitRoute 70.3685 902.284
setEditMode -create_crossover_vias 1
editAddRoute 74.375 902.284
editAddRoute 23.6235 897.61
editCommitRoute 23.6235 897.61
setEditMode -create_crossover_vias 0

setEditMode -nets VDDPST
editAddRoute 480.051 871.233
editAddRoute 480.719 899.279
editAddRoute 460.351 918.645
editAddRoute 285.393 913.303
editAddRoute 208.599 845.189
editAddRoute 70.0345 846.859
editCommitRoute 70.0345 846.859
setEditMode -create_crossover_vias 1
editAddRoute 74.041 842.519
editAddRoute 24.9595 841.183
editCommitRoute 24.9595 841.183
setEditMode -create_crossover_vias 0

setEditMode -nets VSS
editAddRoute 246.996 794.438
editAddRoute 246.328 764.389
editAddRoute 226.629 749.029
editAddRoute 69.7005 742.018
editCommitRoute 69.7005 742.018
setEditMode -create_crossover_vias 1
editAddRoute 73.3735 743.019
editAddRoute 23.29 738.345
editCommitRoute 23.29 738.345
setEditMode -create_crossover_vias 0

setEditMode -nets VDDPST
editAddRoute 480.385 715.975
editAddRoute 483.056 744.021
editAddRoute 463.69 762.719
editAddRoute 287.731 755.707
editAddRoute 208.933 690.933
editAddRoute 69.3665 683.253
editCommitRoute 69.3665 683.253
setEditMode -create_crossover_vias 1
editAddRoute 73.707 683.587
editAddRoute 24.9595 682.251
editCommitRoute 24.9595 682.251
setEditMode -create_crossover_vias 0

setEditMode -nets VDD
editAddRoute 607.219 684.736
editAddRoute 310.111 685.077
editAddRoute 290.69 667.019
editAddRoute 202.103 662.59
editAddRoute 141.796 605.689
editAddRoute 69.2225 601.26
editCommitRoute 69.2225 601.26
setEditMode -create_crossover_vias 1
editAddRoute 73.311 605.008
editAddRoute 42.3055 600.579
editCommitRoute 42.3055 600.579
setEditMode -create_crossover_vias 0

setEditMode -nets VSS
editAddRoute 169.2 558.111
editAddRoute 169.534 533.07
editAddRoute 153.507 522.72
editAddRoute 70.3685 521.384
editCommitRoute 70.3685 521.384
setEditMode -create_crossover_vias 1
editAddRoute 74.709 517.043
editAddRoute 23.6235 515.374
editCommitRoute 23.6235 515.374
setEditMode -create_crossover_vias 0

setEditMode -nets VDDPST
editAddRoute 480.719 559.648
editAddRoute 482.388 526.927
editAddRoute 458.014 513.237
editAddRoute 316.111 511.567
editAddRoute 249.667 444.456
editAddRoute 70.0345 434.106
editCommitRoute 70.0345 434.106
setEditMode -create_crossover_vias 1
editAddRoute 73.707 437.111
editAddRoute 23.9575 432.436
editCommitRoute 23.9575 432.436
setEditMode -create_crossover_vias 0

setEditMode -nets VSS
editAddRoute 247.663 172.536
editAddRoute 245.327 221.952
editAddRoute 186.895 275.041
editAddRoute 165.193 285.058
editAddRoute 89.734 360.517
editAddRoute 69.3665 362.186
editCommitRoute 69.3665 362.186
setEditMode -create_crossover_vias 1
editAddRoute 73.707 360.183
editAddRoute 24.2915 361.184
editCommitRoute 24.2915 361.184
setEditMode -create_crossover_vias 0

# RIGHT (top to bottom)
# Create VDD stripe to the left
setEditMode -nets VDD
editAddRoute 3289.97 3217.07
editAddRoute 3315.11 3216.37
editAddRoute 3343.76 3241.87
editAddRoute 3394.76 3244.66
editAddRoute 3402.44 3228.24
editAddRoute 3415.72 941.666
editCommitRoute 3415.72 941.666

setEditMode -nets VSS
editAddRoute 3678.91 3918.03
editAddRoute 3681.85 3888.62
editAddRoute 3701.33 3866.94
editAddRoute 3777.77 3862.53
editAddRoute 3812.69 3827.98
editAddRoute 3855.69 3819.9
editCommitRoute 3855.69 3819.9
setEditMode -create_crossover_vias 1
editAddRoute 3855.32 3827.61
editAddRoute 3901.63 3826.51
editCommitRoute 3901.63 3826.51
setEditMode -create_crossover_vias 0

setEditMode -nets VSS
editAddRoute 3678.17 3762.93
editAddRoute 3678.54 3735
editAddRoute 3688.1 3727.65
editAddRoute 3799.09 3724.34
editAddRoute 3817.47 3712.95
editAddRoute 3855.69 3706.7
editCommitRoute 3855.69 3706.7
setEditMode -create_crossover_vias 1
editAddRoute 3855.69 3705.96
editAddRoute 3901.26 3712.21
editCommitRoute 3901.26 3712.21
setEditMode -create_crossover_vias 0

setEditMode -nets VDDPST
editAddRoute 3521.61 3606.44
editAddRoute 3522.71 3634.37
editAddRoute 3541.45 3647.6
editAddRoute 3856.06 3656.42
editCommitRoute 3856.06 3656.42
setEditMode -create_crossover_vias 1
editAddRoute 3854.96 3653.11
editAddRoute 3899.79 3651.64
editCommitRoute 3899.79 3651.64
setEditMode -create_crossover_vias 0

setEditMode -nets VSS
editAddRoute 3755.36 3527.05
editAddRoute 3755.72 3552.78
editAddRoute 3767.48 3558.66
editAddRoute 3855.32 3563.8
editCommitRoute 3855.32 3563.8
setEditMode -create_crossover_vias 1
editAddRoute 3854.96 3563.8
editAddRoute 3900.9 3566.01
editCommitRoute 3900.9 3566.01
setEditMode -create_crossover_vias 0

setEditMode -nets VSS
editAddRoute 3681.37 3450.63
editAddRoute 3775.48 3450.3
editAddRoute 3797.19 3463.47
editAddRoute 3804.43 3474
editAddRoute 3820.56 3476.3
editAddRoute 3842.28 3503.28
editAddRoute 3854.78 3503.94
editCommitRoute 3854.78 3503.94
setEditMode -create_crossover_vias 1
editAddRoute 3854.78 3502.3
editAddRoute 3902.16 3503.61
editCommitRoute 3902.16 3503.61
setEditMode -create_crossover_vias 0

setEditMode -nets VDDPST
editAddRoute 3443.33 3373.04
editAddRoute 3445.91 3397.66
editAddRoute 3467.96 3415.3
editAddRoute 3677.08 3417.51
editAddRoute 3686.27 3416.04
editAddRoute 3855.33 3415.67
editCommitRoute 3855.33 3415.67
setEditMode -create_crossover_vias 1
editAddRoute 3853.49 3412.36
editAddRoute 3900.54 3413.47
editCommitRoute 3900.54 3413.47
setEditMode -create_crossover_vias 0

setEditMode -nets VSS
editAddRoute 3677.82 3294.75
editAddRoute 3678.55 3320.48
editAddRoute 3696.19 3330.4
editAddRoute 3855.33 3333.34
editCommitRoute 3855.33 3333.34
setEditMode -create_crossover_vias 1
editAddRoute 3854.97 3337.75
editAddRoute 3900.91 3341.06
editCommitRoute 3900.91 3341.06
setEditMode -create_crossover_vias 0

setEditMode -nets VDDPST
editAddRoute 3444.07 3216.84
editAddRoute 3446.64 3238.15
editAddRoute 3457.67 3248.81
editAddRoute 3461.34 3254.32
editAddRoute 3856.07 3259.84
editCommitRoute 3856.07 3259.84
setEditMode -create_crossover_vias 1
editAddRoute 3855.33 3255.43
editAddRoute 3901.27 3260.57
editCommitRoute 3901.27 3260.57
setEditMode -create_crossover_vias 0

setEditMode -nets VDD
editAddRoute 3411.52 3183.53
editAddRoute 3668.27 3175.85
editAddRoute 3672.81 3188.07
editAddRoute 3855.5 3188.07
editCommitRoute 3855.5 3188.07
setEditMode -create_crossover_vias 1
editAddRoute 3854.1 3188.07
editAddRoute 3899.16 3188.07
editCommitRoute 3899.16 3188.07
setEditMode -create_crossover_vias 0

setEditMode -nets VSS
editAddRoute 3677.82 3139.14
editAddRoute 3680.02 3161.93
editAddRoute 3693.99 3175.16
editAddRoute 3856.07 3182.14
editCommitRoute 3856.07 3182.14
setEditMode -create_crossover_vias 1
editAddRoute 3854.6 3177.73
editAddRoute 3901.64 3180.67
editCommitRoute 3901.64 3180.67
setEditMode -create_crossover_vias 0

setEditMode -nets VDDPST
editAddRoute 3444.8 3057.92
editAddRoute 3445.54 3081.81
editAddRoute 3462.45 3095.04
editAddRoute 3764.19 3096.88
editAddRoute 3782.93 3085.85
editAddRoute 3855.7 3084.38
editCommitRoute 3855.7 3084.38
setEditMode -create_crossover_vias 1
editAddRoute 3855.33 3081.07
editAddRoute 3900.91 3081.81
editCommitRoute 3900.91 3081.81
setEditMode -create_crossover_vias 0

setEditMode -nets VSS
editAddRoute 3677.45 2981.84
editAddRoute 3677.82 3004.99
editAddRoute 3703.18 3022.64
editAddRoute 3855.7 3027.05
editCommitRoute 3855.7 3027.05
setEditMode -create_crossover_vias 1
editAddRoute 3855.33 3029.62
editAddRoute 3902.01 3029.25
editCommitRoute 3902.01 3029.25
setEditMode -create_crossover_vias 0

setEditMode -nets VDDPST
editAddRoute 3444.44 2903.85
editAddRoute 3450.68 2928.84
editAddRoute 3460.97 2936.19
editAddRoute 3855.33 2941.71
editCommitRoute 3855.33 2941.71
setEditMode -create_crossover_vias 1
editAddRoute 3854.23 2945.38
editAddRoute 3899.44 2946.12
editCommitRoute 3899.44 2946.12
setEditMode -create_crossover_vias 0

setEditMode -nets VSS
editAddRoute 3678.55 2824.1
editAddRoute 3682.59 2852.76
editAddRoute 3697.3 2862.32
editAddRoute 3855.33 2870.41
editCommitRoute 3855.33 2870.41
setEditMode -create_crossover_vias 1
editAddRoute 3855.33 2871.14
editAddRoute 3902.01 2871.51
editCommitRoute 3902.01 2871.51
setEditMode -create_crossover_vias 0

setEditMode -nets VDDPST
editAddRoute 3442.97 2744.71
editAddRoute 3447.01 2771.91
editAddRoute 3457.67 2778.52
editAddRoute 3854.97 2784.77
editCommitRoute 3854.97 2784.77
setEditMode -create_crossover_vias 1
editAddRoute 3854.97 2785.51
editAddRoute 3899.8 2788.81
editCommitRoute 3899.8 2788.81
setEditMode -create_crossover_vias 0

setEditMode -nets VDD
editAddRoute 3412.57 2704.56
editAddRoute 3640.67 2709.8
editAddRoute 3709.14 2767.09
editAddRoute 3855.5 2767.43
editCommitRoute 3855.5 2767.43
setEditMode -create_crossover_vias 1
editAddRoute 3855.15 2772.33
editAddRoute 3900.56 2772.68
editCommitRoute 3900.56 2772.68
setEditMode -create_crossover_vias 0

setEditMode -nets VSS
editAddRoute 3677.82 2667.53
editAddRoute 3679.65 2696.56
editAddRoute 3694.36 2707.96
editAddRoute 3855.33 2713.84
editCommitRoute 3855.33 2713.84
setEditMode -create_crossover_vias 1
editAddRoute 3854.97 2712.37
editAddRoute 3901.27 2712.74
editCommitRoute 3901.27 2712.74
setEditMode -create_crossover_vias 0

setEditMode -nets VDDPST
editAddRoute 3445.17 2590.64
editAddRoute 3447.01 2614.53
editAddRoute 3462.08 2624.46
editAddRoute 3855.33 2630.7
editCommitRoute 3855.33 2630.7
setEditMode -create_crossover_vias 1
editAddRoute 3854.6 2632.17
editAddRoute 3900.54 2631.81
editCommitRoute 3900.54 2631.81
setEditMode -create_crossover_vias 0

setEditMode -nets VSS
editAddRoute 3677.08 2513.09
editAddRoute 3679.65 2538.82
editAddRoute 3693.99 2548.38
editAddRoute 3856.07 2555.73
editCommitRoute 3856.07 2555.73
setEditMode -create_crossover_vias 1
editAddRoute 3854.6 2554.26
editAddRoute 3902.38 2553.52
editCommitRoute 3902.38 2553.52
setEditMode -create_crossover_vias 0

setEditMode -nets VDDPST
editAddRoute 3444.07 2433.34
editAddRoute 3446.27 2457.6
editAddRoute 3460.97 2467.52
editAddRoute 3856.44 2474.14
editCommitRoute 3856.44 2474.14
setEditMode -create_crossover_vias 1
editAddRoute 3854.97 2474.14
editAddRoute 3901.27 2474.14
editCommitRoute 3901.27 2474.14
setEditMode -create_crossover_vias 0

setEditMode -nets VSS
editAddRoute 3677.82 2356.16
editAddRoute 3681.86 2383.72
editAddRoute 3695.09 2394.38
editAddRoute 3855.7 2399.9
editCommitRoute 3855.7 2399.9
setEditMode -create_crossover_vias 1
editAddRoute 3855.33 2400.63
editAddRoute 3901.64 2402.84
editCommitRoute 3901.64 2402.84
setEditMode -create_crossover_vias 0

setEditMode -nets VDDPST
editAddRoute 3443.7 2273.47
editAddRoute 3448.11 2301.77
editAddRoute 3460.24 2311.32
editAddRoute 3854.97 2313.89
editCommitRoute 3854.97 2313.89
setEditMode -create_crossover_vias 1
editAddRoute 3854.6 2317.2
editAddRoute 3901.27 2318.3
editCommitRoute 3901.27 2318.3
setEditMode -create_crossover_vias 0

setEditMode -nets VDD
editAddRoute 3412.57 2239.35
editAddRoute 3641.02 2251.58
editAddRoute 3705.99 2296.29
editAddRoute 3855.85 2302.22
editCommitRoute 3855.85 2302.22
setEditMode -create_crossover_vias 1
editAddRoute 3854.45 2303.97
editAddRoute 3900.91 2304.32
editCommitRoute 3900.91 2304.32
setEditMode -create_crossover_vias 0

setEditMode -nets VSS
editAddRoute 3678.18 2199.52
editAddRoute 3678.55 2226.35
editAddRoute 3697.3 2242.89
editAddRoute 3854.97 2246.2
editCommitRoute 3854.97 2246.2
setEditMode -create_crossover_vias 1
editAddRoute 3854.6 2245.46
editAddRoute 3901.64 2245.46
editCommitRoute 3901.64 2245.46
setEditMode -create_crossover_vias 0

setEditMode -nets VDDPST
editAddRoute 3444.07 2120.5
editAddRoute 3448.11 2144.39
editAddRoute 3459.87 2153.21
editAddRoute 3855.7 2159.09
editCommitRoute 3855.7 2159.09
setEditMode -create_crossover_vias 1
editAddRoute 3854.6 2159.09
editAddRoute 3900.54 2161.3
editCommitRoute 3900.54 2161.3
setEditMode -create_crossover_vias 0

setEditMode -nets VDDPST
editAddRoute 3444.8 1965.77
editAddRoute 3445.91 1990.03
editAddRoute 3459.87 2002.52
editAddRoute 3856.07 2001.05
editCommitRoute 3856.07 2001.05
setEditMode -create_crossover_vias 1
editAddRoute 3855.33 2005.83
editAddRoute 3899.44 2005.83
editCommitRoute 3899.44 2005.83
setEditMode -create_crossover_vias 0

setEditMode -nets VDD
editAddRoute 3412.57 1931.33
editAddRoute 3626 1926.44
editAddRoute 3687.48 1983.38
editAddRoute 3855.85 1985.47
editCommitRoute 3855.85 1985.47
setEditMode -create_crossover_vias 1
editAddRoute 3855.5 1992.46
editAddRoute 3900.21 1993.16
editCommitRoute 3900.21 1993.16
setEditMode -create_crossover_vias 0

setEditMode -nets VSS
editAddRoute 3680.02 1888.52
editAddRoute 3680.76 1913.88
editAddRoute 3700.97 1931.52
editAddRoute 3856.8 1936.66
editCommitRoute 3856.8 1936.66
setEditMode -create_crossover_vias 1
editAddRoute 3855.33 1936.66
editAddRoute 3901.27 1937.03
editCommitRoute 3901.27 1937.03
setEditMode -create_crossover_vias 0

setEditMode -nets VSS
editAddRoute 3676.71 1882.27
editAddRoute 3681.49 1863.16
editAddRoute 3689.95 1852.5
editAddRoute 3855.33 1848.46
editCommitRoute 3855.33 1848.46
setEditMode -create_crossover_vias 1
editAddRoute 3855.33 1849.93
editAddRoute 3901.27 1850.66
editCommitRoute 3901.27 1850.66
setEditMode -create_crossover_vias 0

setEditMode -nets VDDPST
editAddRoute 3443.7 1808.4
editAddRoute 3446.64 1781.2
editAddRoute 3457.67 1769.44
editAddRoute 3855.33 1766.87
editCommitRoute 3855.33 1766.87
setEditMode -create_crossover_vias 1
editAddRoute 3854.6 1766.87
editAddRoute 3899.44 1766.87
editCommitRoute 3899.44 1766.87
setEditMode -create_crossover_vias 0

setEditMode -nets VSS
editAddRoute 3678.18 1729.01
editAddRoute 3682.23 1704.39
editAddRoute 3688.84 1695.57
editAddRoute 3856.07 1693.73
editCommitRoute 3856.07 1693.73
setEditMode -create_crossover_vias 1
editAddRoute 3854.6 1692.62
editAddRoute 3900.91 1695.93
editCommitRoute 3900.91 1695.93
setEditMode -create_crossover_vias 0

setEditMode -nets VDDPST
editAddRoute 3443.7 1653.3
editAddRoute 3449.21 1625.73
editAddRoute 3459.87 1611.77
editAddRoute 3856.44 1608.09
editCommitRoute 3856.44 1608.09
setEditMode -create_crossover_vias 1
editAddRoute 3855.7 1609.56
editAddRoute 3901.27 1611.4
editCommitRoute 3901.27 1611.4
setEditMode -create_crossover_vias 0

setEditMode -nets VSS
editAddRoute 3678.18 1571.27
editAddRoute 3680.76 1548.11
editAddRoute 3698.77 1527.9
editAddRoute 3855.7 1516.14
editCommitRoute 3855.7 1516.14
setEditMode -create_crossover_vias 1
editAddRoute 3855.33 1526.8
editAddRoute 3900.91 1527.16
editCommitRoute 3900.91 1527.16
setEditMode -create_crossover_vias 0

editAddRoute 3411.18 1535.63
editAddRoute 3632.64 1537.03
editAddRoute 3698.66 1476.95
editAddRoute 3856.2 1467.52
editCommitRoute 3856.2 1467.52
setEditMode -create_crossover_vias 1
editAddRoute 3853.75 1469.61
editAddRoute 3900.56 1468.91
editCommitRoute 3900.56 1468.91
setEditMode -create_crossover_vias 0

setEditMode -nets VDDPST
editAddRoute 3444.07 1495.92
editAddRoute 3446.64 1469.09
editAddRoute 3456.56 1460.64
editAddRoute 3856.44 1454.03
editCommitRoute 3856.44 1454.03
setEditMode -create_crossover_vias 1
editAddRoute 3854.6 1456.23
editAddRoute 3900.91 1458.07
editCommitRoute 3900.91 1458.07
setEditMode -create_crossover_vias 0

setEditMode -nets VSS
editAddRoute 3677.82 1418.01
editAddRoute 3681.12 1391.55
editAddRoute 3689.95 1382.36
editAddRoute 3855.7 1383.09
editCommitRoute 3855.7 1383.09
setEditMode -create_crossover_vias 1
editAddRoute 3855.33 1378.68
editAddRoute 3900.91 1380.89
editCommitRoute 3900.91 1380.89
setEditMode -create_crossover_vias 0

setEditMode -nets VDDPST
editAddRoute 3444.8 1341.19
editAddRoute 3447.01 1311.06
editAddRoute 3456.93 1302.6
editAddRoute 3856.8 1304.07
editCommitRoute 3856.8 1304.07
setEditMode -create_crossover_vias 1
editAddRoute 3855.7 1297.83
editAddRoute 3900.54 1299.66
editCommitRoute 3900.54 1299.66
setEditMode -create_crossover_vias 0

setEditMode -nets VSS
editAddRoute 3679.29 1260.71
editAddRoute 3680.76 1224.69
editAddRoute 3693.25 1212.56
editAddRoute 3854.97 1217.34
editCommitRoute 3854.97 1217.34
setEditMode -create_crossover_vias 1
editAddRoute 3854.6 1208.52
editAddRoute 3900.17 1211.46
editCommitRoute 3900.17 1211.46
setEditMode -create_crossover_vias 0

setEditMode -nets VDD
editAddRoute 3412.92 1225.38
editAddRoute 3628.1 1219.79
editAddRoute 3697.61 1156.21
editAddRoute 3856.2 1152.02
editCommitRoute 3856.2 1152.02
setEditMode -create_crossover_vias 1
editAddRoute 3854.45 1155.86
editAddRoute 3900.91 1154.81
editCommitRoute 3900.91 1154.81
setEditMode -create_crossover_vias 0

setEditMode -nets VDDPST
editAddRoute 3444.44 1185.29
editAddRoute 3447.74 1157.36
editAddRoute 3456.56 1150.01
editAddRoute 3856.07 1147.8
editCommitRoute 3856.07 1147.8
setEditMode -create_crossover_vias 1
editAddRoute 3855.33 1144.13
editAddRoute 3901.64 1144.49
editCommitRoute 3901.64 1144.49
setEditMode -create_crossover_vias 0

setEditMode -nets VSS
editAddRoute 3677.08 1104.43
editAddRoute 3680.02 1079.44
editAddRoute 3688.84 1073.19
editAddRoute 3855.7 1063.64
editCommitRoute 3855.7 1063.64
setEditMode -create_crossover_vias 1
editAddRoute 3854.97 1068.41
editAddRoute 3900.91 1067.68
editCommitRoute 3900.91 1067.68
setEditMode -create_crossover_vias 0

setEditMode -nets VDDPST
editAddRoute 3443.7 1030.56
editAddRoute 3446.27 1001.16
editAddRoute 3458.4 990.866
editAddRoute 3856.44 989.764
editCommitRoute 3856.44 989.764
setEditMode -create_crossover_vias 1
editAddRoute 3854.6 986.089
editAddRoute 3900.54 987.192
editCommitRoute 3900.54 987.192
setEditMode -create_crossover_vias 0

setEditMode -nets VSS
editAddRoute 3677.08 947.499
editAddRoute 3680.02 924.344
editAddRoute 3691.41 914.42
editAddRoute 3855.33 911.481
editCommitRoute 3855.33 911.481
setEditMode -create_crossover_vias 1
editAddRoute 3854.6 910.378
editAddRoute 3900.91 910.01
editCommitRoute 3900.91 910.01
setEditMode -create_crossover_vias 0

setEditMode -nets VDD
editAddRoute 3412.92 948.303
editAddRoute 3413.27 919.311
editAddRoute 3422.7 911.277
editAddRoute 3516.67 901.146
editAddRoute 3577.1 849.099
editAddRoute 3856.89 842.462
editCommitRoute 3856.89 842.462
setEditMode -create_crossover_vias 1
editAddRoute 3854.8 845.257
editAddRoute 3900.91 844.558
editCommitRoute 3900.91 844.558
setEditMode -create_crossover_vias 0

setEditMode -nets VDDPST
editAddRoute 3445.17 875.757
editAddRoute 3447.74 846.355
editAddRoute 3455.83 838.637
editAddRoute 3856.8 836.064
editCommitRoute 3856.8 836.064
setEditMode -create_crossover_vias 1
editAddRoute 3854.23 833.491
editAddRoute 3900.91 834.962
editCommitRoute 3900.91 834.962
setEditMode -create_crossover_vias 0

setEditMode -nets VSS
editAddRoute 3677.45 793.431
editAddRoute 3680.39 761.456
editAddRoute 3697.66 746.755
editAddRoute 3855.7 740.874
editCommitRoute 3855.7 740.874
setEditMode -create_crossover_vias 1
editAddRoute 3855.7 741.241
editAddRoute 3901.64 740.874
editCommitRoute 3901.64 740.874
setEditMode -create_crossover_vias 0

setEditMode -nets VDDPST
editAddRoute 3447.01 719.19
editAddRoute 3447.01 743.814
editAddRoute 3465.02 756.678
editAddRoute 3516.84 757.413
editAddRoute 3618.28 747.857
editAddRoute 3698.4 694.198
editAddRoute 3855.7 680.967
editCommitRoute 3855.7 680.967
setEditMode -create_crossover_vias 1
editAddRoute 3854.23 684.643
editAddRoute 3901.64 683.172
editCommitRoute 3901.64 683.172
setEditMode -create_crossover_vias 0

setEditMode -nets VSS
editAddRoute 3680.76 636.864
editAddRoute 3680.76 611.504
editAddRoute 3688.47 604.521
editAddRoute 3856.44 603.051
editCommitRoute 3856.44 603.051
setEditMode -create_crossover_vias 1
editAddRoute 3854.23 600.479
editAddRoute 3882.16 600.846
editCommitRoute 3882.16 600.846
setEditMode -create_crossover_vias 0

setEditMode -nets VSS
editAddRoute 3603.18 561.084
editAddRoute 3812.46 565.688
editAddRoute 3829.62 548.11
editAddRoute 3856.82 538.902
editCommitRoute 3856.82 538.902
setEditMode -create_crossover_vias 1
editAddRoute 3856.82 541.831
editAddRoute 3901.61 542.25
editCommitRoute 3901.61 542.25
setEditMode -create_crossover_vias 0

setEditMode -nets VDDPST
editAddRoute 3521.62 482.208
editAddRoute 3524.19 507.567
editAddRoute 3540.36 521.166
editAddRoute 3856.44 520.798
editCommitRoute 3856.44 520.798
setEditMode -create_crossover_vias 1
editAddRoute 3854.6 524.841
editAddRoute 3900.17 525.576
editCommitRoute 3900.17 525.576
setEditMode -create_crossover_vias 0

setEditMode -nets VSS
editAddRoute 3677.82 479.267
editAddRoute 3683.33 456.481
editAddRoute 3692.89 448.027
editAddRoute 3855.7 441.779
editCommitRoute 3855.7 441.779
setEditMode -create_crossover_vias 1
editAddRoute 3854.6 441.045
editAddRoute 3902.01 440.31
editCommitRoute 3902.01 440.31
setEditMode -create_crossover_vias 0

setEditMode -nets VDDPST
editAddRoute 3522.72 479.267
editAddRoute 3527.5 448.763
editAddRoute 3542.2 437.002
editAddRoute 3855.7 429.284
editCommitRoute 3855.7 429.284
setEditMode -create_crossover_vias 1
editAddRoute 3854.6 427.813
editAddRoute 3900.17 427.813
editCommitRoute 3900.17 427.813
setEditMode -create_crossover_vias 0

setEditMode -nets VSS
editAddRoute 3677.82 172.822
editAddRoute 3685.17 223.174
editAddRoute 3724.12 266.91
editAddRoute 3741.03 269.483
editAddRoute 3836.96 361.365
editAddRoute 3856.07 368.716
editCommitRoute 3856.07 368.716
setEditMode -create_crossover_vias 1
editAddRoute 3854.6 365.408
editAddRoute 3902.38 365.04
editCommitRoute 3902.38 365.04
setEditMode -create_crossover_vias 0

# Extra wires to connect all bumps

setEditMode -create_crossover_vias 0

setEditMode -nets VSS
editAddRoute 173.763 3685.77
editAddRoute 325.352 3682.21
editCommitRoute 325.352 3682.21

setEditMode -nets VDDPST
editAddRoute 96.442 3608.45
editAddRoute 97.4595 3561.65
editCommitRoute 97.4595 3561.65

setEditMode -nets VSS
editAddRoute 251.592 3608.45
editAddRoute 254.136 3641.51
editCommitRoute 254.136 3641.51

setEditMode -nets VDDPST
setEditMode -create_crossover_vias 0
editAddRoute 486.098 3529.09
editAddRoute 484.063 3569.28
editAddRoute 514.585 3600.82
editAddRoute 561.893 3602.85
editCommitRoute 561.893 3602.85

setEditMode -nets VDDPST
editAddRoute 94.212 482.098
editAddRoute 93.8995 436.798
editCommitRoute 93.8995 436.798

setEditMode -nets VSS
editAddRoute 171.376 560.512
editAddRoute 325.706 559.574
editCommitRoute 325.706 559.574
editAddRoute 250.728 482.098
editAddRoute 249.791 559.263
editCommitRoute 249.791 559.263

setEditMode -nets VSS
uiSetTool addWire
editAddRoute 3288.04 403.577
editAddRoute 3280.1 490.714
editAddRoute 3248.59 521.085
editAddRoute 3169.4 524.207
editAddRoute 3139.03 493.269
editAddRoute 3137.61 387.399
editCommitRoute 3137.61 387.399

setEditMode -nets VSS
editAddRoute 3760.26 405.472
editAddRoute 3598.72 404.115
editCommitRoute 3598.72 404.115
editAddRoute 3682.88 328.091
editAddRoute 3679.72 404.115
editCommitRoute 3679.72 404.115

setEditMode -nets VDDPST
editAddRoute 3838.55 482.853
editAddRoute 3837.65 529.009
editCommitRoute 3837.65 529.009

setEditMode -nets VDDPST
editAddRoute 3448.32 561.503
editAddRoute 3450.41 725.992
editCommitRoute 3450.41 725.992

setEditMode -nets VSS
editAddRoute 3603.21 3684.86
editAddRoute 3442.63 3681.57
editCommitRoute 3442.63 3681.57

setEditMode -nets VSS
editAddRoute 3602.47 3528.5
editAddRoute 3759.64 3529.28
editCommitRoute 3759.64 3529.28
editAddRoute 3681.44 3607.48
editAddRoute 3680.67 3527.34
editCommitRoute 3680.67 3527.34

setEditMode -nets VDDPST
editAddRoute 3838.23 3607.48
editAddRoute 3838.23 3655.09
editCommitRoute 3838.23 3655.09
editAddRoute 3447.23 3528.89
editAddRoute 3448 3574.57
editAddRoute 3475.1 3605.15
editAddRoute 3523.49 3605.93
editCommitRoute 3523.49 3605.93

setEditMode -nets VSS
editAddRoute 170.675 403.74
editAddRoute 326.159 406.327
editCommitRoute 326.159 406.327
editAddRoute 249.322 326.127
editAddRoute 248.805 403.998
editCommitRoute 248.805 403.998

setEditMode -nets VSS
editAddRoute 250.823 638.987
editAddRoute 322.861 638.566
editAddRoute 358.247 667.634
editAddRoute 429.863 661.736
editAddRoute 455.139 634.354
editAddRoute 456.402 595.597
editAddRoute 429.863 564.423
editAddRoute 322.861 558.947
editCommitRoute 322.861 558.947

setEditMode -net VSS
editAddRoute 252.021 171.863
editAddRoute 373.942 169.386
editCommitRoute 373.942 169.386

setEditMode -nets VSS
editAddRoute 1888.43 405
editAddRoute 2040.25 401.08
editCommitRoute 2040.25 401.08

setEditMode -nets VDDPST
editAddRoute 3366.77 3607.7
editAddRoute 3371.63 3560.14
editAddRoute 3401.84 3528.89
editAddRoute 3446.98 3525.41
editCommitRoute 3446.98 3525.41

setEditMode -nets VDDPST
editAddRoute 558.746 481.581
editAddRoute 563.091 531.683
editAddRoute 543.976 551.087
editAddRoute 478.236 556.3
editCommitRoute 478.236 556.3

setEditMode -nets VDDPST
editAddRoute 407.413 483.726
editAddRoute 407.813 505.371
editCommitRoute 407.813 505.371

setEditMode -nets VDDPST
editAddRoute 481.834 3211.79
editAddRoute 483.538 3055.4
editCommitRoute 483.538 3055.4

setEditMode -nets VDDPST
editAddRoute 90.501 481.743
editAddRoute 93.762 436.589
editCommitRoute 93.762 436.589
