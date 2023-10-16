#=========================================================================
# power-strategy-fullmesh.tcl
#=========================================================================
# This script implements a full power mesh for a hierarchical block design. 
# In sub-block design, we use {m1, m2, ..., m7, m8} to create power grids.
# In hierarchical design, we use all sub-block layers plus gmz to create 
# top level power grids. This strategy allows easy integration by simply 
# dropping down Vias from gmz (hierarchical) to m8 (sub-block). Note that 
# M1 stdcell power rails are horizontal and M2 preferred routing direction 
# is also horizontal. Hence, we create M2 power stripes directly on top of 
# M1 (fully overlapped) and put via staples along them.
# 
# Author : Po-Han Chen
# Date   : March 30, 2023
#
# Taken from custom-power-leaf/power-strategy.tcl and modified for
# hierarchical blocks by Alex Carsello on 10/12/23.

#-------------------------------------------------------------------------
# Stdcell power rail preroute
#-------------------------------------------------------------------------
# Generate horizontal stdcell preroutes

sroute -nets {VDD VSS}

#-------------------------------------------------------------------------
# Shorter names from the ADK
#-------------------------------------------------------------------------

set pmesh_bot $ADK_POWER_MESH_BOT_LAYER
set pmesh_top $ADK_POWER_MESH_TOP_LAYER

#-------------------------------------------------------------------------
# M2 power staples
#-------------------------------------------------------------------------
set m1_rail_width [dbGet [dbGet -p top.nets.swires.shape followpin].width]
set m1_rail_width [lindex $m1_rail_width 0]
set poly_pitch [dbGet top.fPlan.coreSite.size_x]

# At the design level, the expectation is that M2 should be fully strapped
# on power M1 with V1 placed every alternate poly pitch
set v1_x_pitch [expr $poly_pitch * 4]
set v1_x_offset_vss [expr $poly_pitch * 2]
set v1_x_offset_vdd [expr $poly_pitch * 3]

## Select the existing followpin routing and duplicate it on M2
deselectAll
editSelect -shape FOLLOWPIN
editDuplicate -layer_horizontal m2 -layer_vertical m2

## Delete auto-generated Vias, because we will insert Vias manually
deselectAll
editSelect -shape FOLLOWPIN
editPowerVia \
    -delete_vias 1 \
    -between_selected_wires 1 \
    -bottom_layer m1 \
    -top_layer m2 \
    -skip_via_on_wire_shape {Ring Blockring Stripe Corewire Blockwire Iowire Padring Fillwire Noshape} \
    -orthogonal_only 0

## Manually insert Vias between M1 & M2
foreach pnet {VDD VSS} {
    if { $pnet == "VDD" } {
        set v1_x_offset $v1_x_offset_vdd
    } else {
        set v1_x_offset $v1_x_offset_vss
    }
    # get the bboxes of the sWires that are on M2
    set power_rails_bboxes [dbGet [dbGet -p2 [dbGet -p top.nets.name $pnet].sWires.layer.name m2].box]
    foreach power_rails_bbox $power_rails_bboxes {
        # for easier access
        set llx [lindex $power_rails_bbox 0]
        set lly [lindex $power_rails_bbox 1]
        set urx [lindex $power_rails_bbox 2]
        set ury [lindex $power_rails_bbox 3]
        # compute the initial position of vias
        set x [expr $llx + $v1_x_offset]
        set y [expr $lly + $m1_rail_width / 2]
        # staple through
        while { ${x} <= ${urx} } {
            add_via -net $pnet -pt $x $y -via $ADK_M1_M2_POWER_VIA
            set x [expr {$x + $v1_x_pitch}]
        }
    }
}

#-------------------------------------------------------------------------
# Adding Power Mesh
#-------------------------------------------------------------------------
set prev_layer m2
set i 0
foreach layer { m3 m4 m5 m6 m7 m8 gmz} {
    # configure via gen
    setViaGenMode -reset
    setViaGenMode -viarule_preference default
    setViaGenMode -ignore_DRC false
    # configure stripe gen
    setAddStripeMode -reset
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
    if { $layer == "m5" || $layer == "m6" } {
        # for m5 and m6, don't extend the stripes to the design boundary
        # because there are pins
        addStripe \
            -nets                {VSS VDD} \
            -layer               $layer \
            -direction           $stripe_direction \
            -width               $stripe_width \
            -start_offset        $stripe_offset \
            -spacing             $stripe_spacing \
            -set_to_set_distance $stripe_interset_pitch
    } else {
        addStripe \
            -nets                {VSS VDD} \
            -layer               $layer \
            -direction           $stripe_direction \
            -width               $stripe_width \
            -start_offset        $stripe_offset \
            -spacing             $stripe_spacing \
            -set_to_set_distance $stripe_interset_pitch \
            -extend_to           design_boundary
    }
    # update previous metal layer
    set prev_layer $layer
    set i [expr $i + 1]
}
