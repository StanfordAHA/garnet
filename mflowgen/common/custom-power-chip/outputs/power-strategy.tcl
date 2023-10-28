#=========================================================================
# power-strategy-fullmesh.tcl
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
# Date   : March 30, 2023

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

# ## Select the existing followpin routing and duplicate it on M2
# deselectAll
# editSelect -shape FOLLOWPIN
# editDuplicate -layer_horizontal m2 -layer_vertical m2

# ## Delete auto-generated Vias, because we will insert Vias manually
# deselectAll
# editSelect -shape FOLLOWPIN
# editPowerVia \
#     -delete_vias 1 \
#     -between_selected_wires 1 \
#     -bottom_layer m1 \
#     -top_layer m2 \
#     -skip_via_on_wire_shape {Ring Blockring Stripe Corewire Blockwire Iowire Padring Fillwire Noshape} \
#     -orthogonal_only 0

# ## Manually insert Vias between M1 & M2
# foreach pnet {VDD VSS} {
#     if { $pnet == "VDD" } {
#         set v1_x_offset $v1_x_offset_vdd
#     } else {
#         set v1_x_offset $v1_x_offset_vss
#     }
#     # get the bboxes of the sWires that are on M2
#     set power_rails_bboxes [dbGet [dbGet -p2 [dbGet -p top.nets.name $pnet].sWires.layer.name m2].box]
#     foreach power_rails_bbox $power_rails_bboxes {
#         # for easier access
#         set llx [lindex $power_rails_bbox 0]
#         set lly [lindex $power_rails_bbox 1]
#         set urx [lindex $power_rails_bbox 2]
#         set ury [lindex $power_rails_bbox 3]
#         # compute the initial position of vias
#         set x [expr $llx + $v1_x_offset]
#         set y [expr $lly + $m1_rail_width / 2]
#         # staple through
#         while { ${x} <= ${urx} } {
#             add_via -net $pnet -pt $x $y -via $ADK_M1_M2_POWER_VIA
#             set x [expr {$x + $v1_x_pitch}]
#         }
#     }
# }

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
# Adding Power Mesh
#-------------------------------------------------------------------------
set prev_layer m2
set i 0
foreach layer { m3 m4 m5 m6 m7 m8 gmz} {

    # configure via gen
    setViaGenMode -reset
    setViaGenMode -viarule_preference default
    # setViaGenMode -ignore_DRC true

    # configure stripe gen
    setAddStripeMode -reset
    # setAddStripeMode -ignore_DRC true
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
# RDL Power Mesh
#-------------------------------------------------------------------------
set vert_pitch [dbGet top.fPlan.coreSite.size_y]
set hori_pitch [dbGet top.fPlan.coreSite.size_x]

set pwr_gm0_width   2.0
set pwr_gm0_spacing 4.0
set pwr_gm0_offset  [expr $pwr_gm0_spacing + 0.5 * $pwr_gm0_width]
set pwr_gm0_interset_pitch [expr 2 * ($pwr_gm0_width + $pwr_gm0_spacing)]

set pwr_area_llx [expr $hori_pitch * 1310]
set pwr_area_lly [expr $vert_pitch * 218]
set pwr_area_urx [expr [dbGet top.fPlan.box_urx] - $hori_pitch * 1310]
set pwr_area_ury [expr [dbGet top.fPlan.box_ury] - $vert_pitch * 216]

setViaGenMode -reset
# setViaGenMode -ignore_DRC true
# setAddStripeMode -ignore_DRC true
setAddStripeMode -stacked_via_bottom_layer gmz \
                 -stacked_via_top_layer    gm0

# You may want to add this back later:
# -area                "$pwr_area_llx $pwr_area_lly $pwr_area_urx $pwr_area_ury" \
# For TMA2, just cover the full core area 
addStripe \
        -nets                {VSS VDD} \
        -layer               gm0 \
        -direction           horizontal \
        -width               $pwr_gm0_width \
        -start_offset        $pwr_gm0_offset \
        -spacing             $pwr_gm0_spacing \
        -set_to_set_distance $pwr_gm0_interset_pitch

set pwr_gmb_width [dbGet [dbGet -p head.layers.name gmb].maxWidth]
set pwr_gmb_offset 0
set pwr_gmb_spacing 65.976
set pwr_gmb_interset_pitch [expr 2 * ($pwr_gmb_width + $pwr_gmb_spacing)]

set pwr_area_llx 552.792
set pwr_area_lly 852.66
set pwr_area_urx [expr [dbGet top.fPlan.box_urx] - $pwr_area_llx]
set pwr_area_ury [expr [dbGet top.fPlan.box_ury] - $pwr_area_lly]

setAddStripeMode -stacked_via_bottom_layer gm0 \
                 -stacked_via_top_layer    gmb

# setViaGenMode -ignore_DRC true
# setAddStripeMode -ignore_DRC true
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
# Pad / Bump Power Routing: Ring
#-------------------------------------------------------------------------
# set pwr_ring_layer         gm0
# set pwr_ring_layer_obj     [dbGet -p head.layers.name $pwr_ring_layer]
# set pwr_ring_width         [dbGet $pwr_ring_layer_obj.maxWidth]
# set pwr_ring_spacing       [expr 2 * [dbGet $pwr_ring_layer_obj.minSpacing]]
# set pwr_ring_offset_top    40.0
# set pwr_ring_offset_bottom 40.0
# set pwr_ring_offset_left   44.0
# set pwr_ring_offset_right  44.0

# # We don't want to connect to other power mesh
# setAddRingMode -reset
# setAddRingMode -stacked_via_bottom_layer $pwr_ring_layer \
#                -stacked_via_top_layer    $pwr_ring_layer \
#                -skip_via_on_wire_shape {Blockring Stripe Padring Ring Noshape}
# addRing \
#     -nets {VSS VDDPST VDD} \
#     -layer $pwr_ring_layer \
#     -width $pwr_ring_width \
#     -spacing $pwr_ring_spacing \
#     -offset "top    -$pwr_ring_offset_top \
#              bottom -$pwr_ring_offset_bottom \
#              left   -$pwr_ring_offset_left \
#              right  -$pwr_ring_offset_right"

#-------------------------------------------------------------------------
# Pad / Bump Power Routing: Stripe
#-------------------------------------------------------------------------
# Ring offset is relative to the core box
# but here we need to compute the offset relative to the pads
# and there is a small pitch gap between the pads and the core box
# (this is defined in the floorplan.tcl)
# set pwr_ring_offset_top    [expr $pwr_ring_offset_top    + 2 * $vert_pitch]
# set pwr_ring_offset_bottom [expr $pwr_ring_offset_bottom + 2 * $vert_pitch]
# set pwr_ring_offset_left   [expr $pwr_ring_offset_left   + 8 * $hori_pitch]
# set pwr_ring_offset_right  [expr $pwr_ring_offset_right  + 8 * $hori_pitch]

# setAddStripeMode -reset
# setAddStripeMode -ignore_DRC true
# setAddStripeMode -stacked_via_bottom_layer gm0 \
#                  -stacked_via_top_layer    gmb

# foreach side {top bottom left right} {
#     set pad_objs [dbGet -p top.insts.name IOPAD_$side*]
#     foreach pad_obj $pad_objs {
#         set pad_inst_name [dbGet $pad_obj.name]
#         set pad_cell_name [dbGet $pad_obj.cell.name]
#         set pad_llx [dbGet $pad_obj.box_llx]
#         set pad_lly [dbGet $pad_obj.box_lly]
#         set pad_urx [dbGet $pad_obj.box_urx]
#         set pad_ury [dbGet $pad_obj.box_ury]
#         set i 0
#         foreach pwr_io { vss* vccio vcc } {
#             set sbox_llx $pad_llx
#             set sbox_lly $pad_lly
#             set sbox_urx $pad_urx
#             set sbox_ury $pad_ury
#             if {$side eq "top"} {
#                 set sbox_lly [expr $sbox_lly - $pwr_ring_offset_top - ($i+1)*$pwr_ring_width - $i*$pwr_ring_spacing]
#                 set stripe_direction "vertical"
#                 set pad_length [dbGet $pad_obj.box_sizex]
#             } elseif {$side eq "bottom"} {
#                 set sbox_ury [expr $sbox_ury + $pwr_ring_offset_bottom + ($i+1)*$pwr_ring_width + $i*$pwr_ring_spacing]
#                 set stripe_direction "vertical"
#                 set pad_length [dbGet $pad_obj.box_sizex]
#             } elseif {$side eq "left"} {
#                 set sbox_urx [expr $sbox_urx + $pwr_ring_offset_left + ($i+1)*$pwr_ring_width + $i*$pwr_ring_spacing]
#                 set stripe_direction "horizontal"
#                 set pad_length [dbGet $pad_obj.box_sizey]
#             } elseif {$side eq "right"} {
#                 set sbox_llx [expr $sbox_llx - $pwr_ring_offset_right - ($i+1)*$pwr_ring_width - $i*$pwr_ring_spacing]
#                 set stripe_direction "horizontal"
#                 set pad_length [dbGet $pad_obj.box_sizey]
#             }
#             # compute the stripe width and offset
#             if {[string match "*SUPPLY*" $pad_inst_name]} {
#                 # SUPPLY pad
#                 if {$pwr_io eq "vss*"} {
#                     set stripe_net VSS
#                 } elseif {$pwr_io eq "vccio"} {
#                     set stripe_net VDDPST
#                 } elseif {$pwr_io eq "vcc"} {
#                     set stripe_net VDD
#                 }
#                 # based on i, compute the offset
#                 set stripe_width 12.0
#                 set space [expr ($pad_length - $stripe_width*3) / 2]
#                 set stripe_offset [expr $i*($space + $stripe_width)]
#             } else {
#                 # SIGNAL pad
#                 set param_vss_stripe_width 8.0
#                 set param_vcc_stripe_width 12.0
#                 if {$side eq "top" || $side eq "bottom"} {
#                     set param_space 1.3
#                 } elseif {$side eq "left" || $side eq "right"} {
#                     set param_space 2.47
#                 }
#                 if {$pwr_io eq "vss*"} {
#                     set stripe_net VSS
#                     set stripe_width 8.0
#                     set stripe_offset 0
#                 } elseif {$pwr_io eq "vccio"} {
#                     set stripe_net VDDPST
#                     set stripe_width 8.0
#                     set stripe_offset [expr $param_vss_stripe_width + $param_space]
#                 } elseif {$pwr_io eq "vcc"} {
#                     set stripe_net VDD
#                     set stripe_width 12.0
#                     set stripe_offset [expr $pad_length - $param_vcc_stripe_width]
#                 }
#             }
            
#             # add the stripe
#             addStripe \
#                 -area "$sbox_llx $sbox_lly $sbox_urx $sbox_ury" \
#                 -direction $stripe_direction \
#                 -layer gmb \
#                 -nets $stripe_net \
#                 -width $stripe_width \
#                 -start_offset $stripe_offset \
#                 -number_of_sets 1
#             # advanced to the next power net
#             incr i
#         }
#     }
# }
