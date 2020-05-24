#=========================================================================
# power-strategy-dualmesh.tcl
#=========================================================================
# This script implements a dual power mesh, with a fine-grain power mesh
# on the lower metal layers and a coarse-grain power mesh on the upper
# metal layers. Note that M2/M3 are expected to be horizontal/vertical,
# and the lower metal layer of the coarse power mesh is expected to be
# horizontal.
#
# Author : ALex Carsello
# Date   : March 26, 2020

#-------------------------------------------------------------------------
# M1 power stripes
#-------------------------------------------------------------------------
set M1_width 0.09
                                                          
setViaGenMode -reset
setViaGenMode -viarule_preference default
setViaGenMode -ignore_DRC true

setAddStripeMode -reset
setAddStripeMode -stacked_via_bottom_layer 1 \
                 -stacked_via_top_layer    1 \
                 -ignore_DRC true                           

set stripeLlx [dbGet top.fPlan.coreBox_llx]
set stripeLly [expr [dbGet top.fPlan.coreBox_lly] - ($M1_width / 2)]
set stripeUrx [dbGet top.fPlan.coreBox_urx]
set stripeUry [expr [dbGet top.fPlan.coreBox_ury] + ($M1_width)]
setAddStripeMode -area [list $stripeLlx $stripeLly $stripeUrx $stripeUry]

addStripe \
  -spacing [expr [dbGet top.fPlan.coreSite.size_y] - $M1_width]   \
  -set_to_set_distance [expr 2 * [dbGet top.fPlan.coreSite.size_y]]   \
  -direction horizontal   \
  -layer M1   \
  -width $M1_width \
  -nets {VDD VSS}

#-------------------------------------------------------------------------
# Shorter names from the ADK
#-------------------------------------------------------------------------

set pmesh_bot $ADK_POWER_MESH_BOT_LAYER
set pmesh_top $ADK_POWER_MESH_TOP_LAYER

#-------------------------------------------------------------------------
# M3 power stripe settings
#-------------------------------------------------------------------------
# We are using addStripe to add sets of stripes (a set includes both VSS
# and VDD).
#
# Set variables to space VSS and VDD straps evenly throughout the chip.
#
#     VSS    VDD    VSS
#     | |    | |    | |
#     | |    | |    | |
#     | |    | |    | |
#
#     _______ <---- $M3_str_pitch
#     ______________
#        ____   ^
#     ___  ^    |
#      ^   |    +-- $M3_str_interset_pitch
#      |   +------- $M3_str_intraset_spacing
#      +----------- $M3_str_width
#
# - M3_str_intraset_spacing : Space between VSS/VDD, chosen for constant
#                             pitch across all VSS and VDD stripes
# - M3_str_interset_pitch   : Pitch between same-signal stripes
#
# - M3_str_offset           : Offset from left edge of core to center the
#                             M3 stripe between vertical M3 routing tracks
#
# - M3_str_width            : M3 stripe width
# - M3_str_pitch            : Choosing an arbitrary M3 pitch that is a
#                             multiple of M3 signal pitch for now

# Get M3 min width and signal routing pitch as defined in the LEF

set M3_min_width    [dbGet [dbGetLayerByZ 3].minWidth]
set M3_route_pitchX [dbGet [dbGetLayerByZ 3].pitchX]

# Set M3 stripe variables

set M3_str_width            [expr  3 * $M3_min_width]
set M3_str_pitch            [expr 10 * $M3_route_pitchX]

set M3_str_intraset_spacing [expr $M3_str_pitch - $M3_str_width]
set M3_str_interset_pitch   [expr 2*$M3_str_pitch]

set M3_str_offset           [expr $M3_str_pitch + $M3_route_pitchX/2 - $M3_str_width/2]

setViaGenMode -reset
setViaGenMode -viarule_preference default
setViaGenMode -ignore_DRC true

setAddStripeMode -reset
setAddStripeMode -stacked_via_bottom_layer 1 \
                 -stacked_via_top_layer    3 \
                 -ignore_DRC true

# Ensure M3 stripes cross fully over bottom M1 stripe to prevent DRCs
set stripeLlx [dbGet top.fPlan.coreBox_llx]
set stripeLly [expr [dbGet top.fPlan.coreBox_lly] - [dbGet [dbGetLayerByZ 1].pitchY]]
set stripeUrx [dbGet top.fPlan.coreBox_urx]
set stripeUry [expr [dbGet top.fPlan.coreBox_ury] + [dbGet [dbGetLayerByZ 1].pitchY]]
setAddStripeMode -area [list $stripeLlx $stripeLly $stripeUrx $stripeUry]

addStripe -nets {VSS VDD} -layer 3 -direction vertical \
    -width $M3_str_width                                \
    -spacing $M3_str_intraset_spacing                   \
    -set_to_set_distance $M3_str_interset_pitch         \
    -start_offset $M3_str_offset

#-------------------------------------------------------------------------
# M5 straps over memory
#-------------------------------------------------------------------------
# The M5 straps are required over the memory because the M4 power straps
# inside the SRAMs are horizontal, and our M8 strap in the coarse power
# mesh are also horizontal. The M5 vertical straps are needed to form an
# intersection with the M8 straps where the tool can place via stacks.
#
# Parameters:
#
# - M5_str_width            : Chose 6x M3 stripe thickness to make stripe
#                             thickness "graduated" as we go up.
# - M5_str_pitch            : Arbitrarily choosing the pitch between stripes
# - M5_str_intraset_spacing : Space between VSS/VDD, chosen for constant
#                             pitch across VSS and VDD stripes
# - M5_str_interset_pitch   : Pitch between same-signal stripes

set M5_str_width            [expr 6 * $M3_str_width]
set M5_str_pitch            [expr 5 * $M3_str_pitch]
set M5_str_intraset_spacing [expr $M5_str_pitch - $M5_str_width]
set M5_str_interset_pitch   [expr 2*$M5_str_pitch]

setViaGenMode -reset
setViaGenMode -viarule_preference default
setViaGenMode -ignore_DRC false

setAddStripeMode -reset
setAddStripeMode -stacked_via_bottom_layer M4 \
                 -stacked_via_top_layer    M5 \
                 -ignore_DRC false

set srams [get_cells -quiet -hier -filter {is_memory_cell==true}]
foreach_in_collection block $srams {
    selectInst $block
    addStripe -nets {VSS VDD} -layer M5 -direction vertical \
        -width $M5_str_width                                \
        -spacing $M5_str_intraset_spacing                   \
        -set_to_set_distance $M5_str_interset_pitch         \
        -start_offset 1                                     \
        -stop_offset 1                                      \
        -area [dbGet selected.box]
    deselectAll
}

#-------------------------------------------------------------------------
# Power mesh bottom settings (horizontal)
#-------------------------------------------------------------------------
# - pmesh_bot_str_width            : 8X thickness compared to M3
# - pmesh_bot_str_pitch            : Arbitrarily choosing the stripe pitch
# - pmesh_bot_str_intraset_spacing : Space between VSS/VDD, choosing
#                                    constant pitch across VSS/VDD stripes
# - pmesh_bot_str_interset_pitch   : Pitch between same-signal stripes

set pmesh_bot_str_width [expr  8 * $M3_str_width]
set pmesh_bot_str_pitch [expr 10 * $M3_str_pitch]

set pmesh_bot_str_intraset_spacing [expr $pmesh_bot_str_pitch - $pmesh_bot_str_width]
set pmesh_bot_str_interset_pitch   [expr 2*$pmesh_bot_str_pitch]

setViaGenMode -reset
setViaGenMode -viarule_preference default
setViaGenMode -ignore_DRC false

setAddStripeMode -reset
setAddStripeMode -stacked_via_bottom_layer 3 \
                 -stacked_via_top_layer    $pmesh_top \
                 -ignore_DRC false

# Add the stripes
#
# Use -start to offset the stripes slightly away from the core edge.
# Allow same-layer jogs to connect stripes to the core ring if some
# blockage is in the way (e.g., connections from core ring to pads).
# Restrict any routing around blockages to use only layers for power.

addStripe -nets {VSS VDD} -layer $pmesh_bot -direction horizontal \
    -width $pmesh_bot_str_width                                   \
    -spacing $pmesh_bot_str_intraset_spacing                      \
    -set_to_set_distance $pmesh_bot_str_interset_pitch            \
    -max_same_layer_jog_length $pmesh_bot_str_pitch               \
    -padcore_ring_bottom_layer_limit $pmesh_bot                   \
    -padcore_ring_top_layer_limit $pmesh_top                      \
    -start [expr $pmesh_bot_str_pitch]                            \
    -stop 4000

# Add M8 stripes to connect to dragonphy
# Stripes for bottom half of phy block
set bottom 4101.96; set top 4400
addStripe -nets {VDD VSS } \
    -layer M8 -direction horizontal -width 2 -spacing 1 \
    -start $bottom \
    -set_to_set_distance [expr 12.295 - 0.279 - 0.016]\
    -switch_layer_over_obs 0 \
    -max_same_layer_jog_length 2 \
    -padcore_ring_top_layer_limit AP -padcore_ring_bottom_layer_limit M1 \
    -block_ring_top_layer_limit M8 -block_ring_bottom_layer_limit M1 \
    -use_wire_group 0 -snap_wire_center_to_grid none \
    -stop $top

# Stripes for top half of phy block. There are eight groups of wires,
# each consisting of four VDD/VSS pairs.
set bottom 4421.34
set top [expr $bottom + 34]
set delta [expr 39.452 - 0.307 + 0.023 ]
foreach i { 0 1 2 3 4 5 6 7 8 } {

    addStripe -nets {VSS VDD } \
        -layer M8 -direction horizontal -width 2 -spacing 1 \
        -start $bottom \
        -set_to_set_distance [expr 7.15 - 0.15] \
        -switch_layer_over_obs 0 \
        -max_same_layer_jog_length 2 \
        -padcore_ring_top_layer_limit AP -padcore_ring_bottom_layer_limit M1 \
        -block_ring_top_layer_limit M8 -block_ring_bottom_layer_limit M1 \
        -use_wire_group 0 -snap_wire_center_to_grid none \
        -stop $top

    set bottom [expr $bottom + $delta]
    set top    [expr $bottom + 34]
}


# Delete the two stray wires where pins are missing at the top right.
set a { 50 4762 1360 4768 }
editDelete -net VDD -layer M8 -area $a
editDelete -net VSS -layer M8 -area $a

#-------------------------------------------------------------------------
# Power mesh top settings (vertical)
#-------------------------------------------------------------------------
# - pmesh_top_str_width            : 16X thickness compared to M3
# - pmesh_top_str_pitch            : Arbitrarily choosing the stripe pitch
# - pmesh_top_str_intraset_spacing : Space between VSS/VDD, choosing
#                                    constant pitch across VSS/VDD stripes
# - pmesh_top_str_interset_pitch   : Pitch between same-signal stripes

set pmesh_top_str_width [expr 16 * $M3_str_width]
set pmesh_top_str_pitch [expr 20 * $M3_str_pitch] ; # Arbitrary

set pmesh_top_str_intraset_spacing [expr $pmesh_top_str_pitch - $pmesh_top_str_width]
set pmesh_top_str_interset_pitch   [expr 2*$pmesh_top_str_pitch]

setViaGenMode -reset
setViaGenMode -viarule_preference default
setViaGenMode -ignore_DRC false

setAddStripeMode -reset
setAddStripeMode -stacked_via_bottom_layer $pmesh_bot \
                 -stacked_via_top_layer    $pmesh_top \
                 -ignore_DRC false

# Add the stripes
#
# Use -start to offset the stripes slightly away from the core edge.
# Allow same-layer jogs to connect stripes to the core ring if some
# blockage is in the way (e.g., connections from core ring to pads).
# Restrict any routing around blockages to use only layers for power.

addStripe -nets {VSS VDD} -layer $pmesh_top -direction vertical \
    -width $pmesh_top_str_width                                 \
    -spacing $pmesh_top_str_intraset_spacing                    \
    -set_to_set_distance $pmesh_top_str_interset_pitch          \
    -max_same_layer_jog_length $pmesh_top_str_pitch             \
    -padcore_ring_bottom_layer_limit $pmesh_bot                 \
    -padcore_ring_top_layer_limit $pmesh_top                    \
    -start [expr $pmesh_top_str_pitch/2]

# RDL Layer Power stripes (Deliver power from bumps to pmesh_top)
setViaGenMode -reset
setViaGenMode -viarule_preference default
setViaGenMode -ignore_DRC true

setAddStripeMode -reset
setAddStripeMode -stacked_via_bottom_layer $pmesh_top \
                 -stacked_via_top_layer    AP \
                 -ignore_DRC true

addStripe -nets {VDD VSS} \
  -over_bumps 1 \
  -layer AP -direction horizontal \
  -width 30.0 -spacing 20.0 -number_of_sets 1 \
  -start_from left \
  -area {1050.0 1050.0 3850.0 3850.0}


