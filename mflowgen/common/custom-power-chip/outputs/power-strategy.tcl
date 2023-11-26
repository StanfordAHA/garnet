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
