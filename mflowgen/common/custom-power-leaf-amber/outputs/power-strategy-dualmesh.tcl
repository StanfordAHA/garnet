#=========================================================================
# power-strategy-dualmesh.tcl
#=========================================================================
# This script implements a dual power mesh, with a fine-grain power mesh
# on the lower metal layers and a coarse-grain power mesh on the upper
# metal layers. Note that M2/M3 are expected to be horizontal/vertical,
# and the lower metal layer of the coarse power mesh is expected to be
# horizontal.
#
# Author : Christopher Torng
# Date   : March 26, 2018

#-------------------------------------------------------------------------
# Stdcell power rail preroute
#-------------------------------------------------------------------------
# Generate horizontal stdcell preroutes

if $::env(PWR_AWARE) {
 set power_nets {VDD_SW VSS VDD}
 # VDD is 2nd power net so that it can 
 # be available above and below the SRAMs
 set aon_power_nets {VSS VDD}
 set sw_power_nets {VDD_SW}
 sroute -nets $power_nets
} else {
 set power_nets {VDD VSS} 
 sroute -nets $power_nets 
}

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

if $::env(PWR_AWARE) {
  set M3_str_intraset_spacing [expr ($M3_str_pitch - 2*$M3_str_width)/2]
} else {
  set M3_str_intraset_spacing [expr $M3_str_pitch - $M3_str_width]
}

set M3_str_interset_pitch   [expr 2*$M3_str_pitch]

set M3_str_offset           [expr $M3_str_pitch + $M3_route_pitchX/2 - $M3_str_width/2]

setViaGenMode -reset
setViaGenMode -viarule_preference default
setViaGenMode -ignore_DRC false

setAddStripeMode -reset
setAddStripeMode -stacked_via_bottom_layer 1 \
                 -stacked_via_top_layer    3

# Ensure M3 stripes cross fully over bottom M1 stripe to prevent DRCs
set stripeLlx [dbGet top.fPlan.coreBox_llx]
set stripeLly [expr [dbGet top.fPlan.coreBox_lly] - [dbGet [dbGetLayerByZ 1].pitchY]]
set stripeUrx [dbGet top.fPlan.coreBox_urx]
set stripeUry [expr [dbGet top.fPlan.coreBox_ury] + [dbGet [dbGetLayerByZ 1].pitchY]]

if $::env(PWR_AWARE) {
  setAddStripeMode -area [list $stripeLlx $stripeLly $stripeUrx $stripeUry] -ignore_nondefault_domains true

  # M3 stripes: VDD_SW and VSS (GND)

  addStripe -nets {VDD_SW VSS} -layer 3 -direction vertical \
    -width $M3_str_width                        \
    -spacing $M3_str_intraset_spacing           \
    -set_to_set_distance $M3_str_interset_pitch \
    -start_offset $M3_str_offset

  # M3 stripes: VDD

  # E.g. sparsity 2 means half as many VDD stripes, 3 means one third etc.
  set VDD_SPARSITY $vdd_m3_stripe_sparsity
  echo "Using VDD_SPARSITY=$VDD_SPARSITY"

  set stripe_to_stripe_pitch [expr ($M3_str_intraset_spacing + $M3_str_width)]
  set M3_VDD_begin  [expr $M3_str_offset + 2 *  $stripe_to_stripe_pitch ]
  set VDD_spacing [expr $VDD_SPARSITY * $M3_str_interset_pitch]

  addStripe -nets {VDD} -layer 3 -direction vertical \
    -width $M3_str_width              \
    -set_to_set_distance $VDD_spacing \
    -start_offset $M3_VDD_begin

} else {
  setAddStripeMode -area [list $stripeLlx $stripeLly $stripeUrx $stripeUry]

  addStripe -nets $power_nets -layer 3 -direction vertical \
    -width $M3_str_width                        \
    -spacing $M3_str_intraset_spacing           \
    -set_to_set_distance $M3_str_interset_pitch \
    -start_offset $M3_str_offset
}


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
setViaGenMode -ignore_DRC 0

setAddStripeMode -reset
setAddStripeMode -stacked_via_bottom_layer M4 \
                 -stacked_via_top_layer    M5

set srams [get_cells -quiet -hier -filter {is_memory_cell==true}]
foreach_in_collection block $srams {
    selectInst $block
    addStripe -nets $power_nets -layer M5 -direction vertical \
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


if $::env(PWR_AWARE) {
    # To allow VDD stripe at top and bottom the SRAM
    set pmesh_bot_str_pitch [expr 6 * $M3_str_pitch]
} else {
    set pmesh_bot_str_pitch [expr 10 * $M3_str_pitch]
}

if $::env(PWR_AWARE) {
   set pmesh_bot_str_intraset_spacing [expr ($pmesh_bot_str_pitch - 2*$pmesh_bot_str_width)/2]
} else {
   set pmesh_bot_str_intraset_spacing [expr $pmesh_bot_str_pitch - $pmesh_bot_str_width]
}
set pmesh_bot_str_interset_pitch   [expr 2*$pmesh_bot_str_pitch]

setViaGenMode -reset
setViaGenMode -viarule_preference default
setViaGenMode -ignore_DRC false

setAddStripeMode -reset
setAddStripeMode -reset
if $::env(PWR_AWARE) {
   setAddStripeMode -stacked_via_bottom_layer 3 \
                 -stacked_via_top_layer    $pmesh_top \
                 -ignore_nondefault_domains true

addStripe -nets $aon_power_nets -layer $pmesh_bot -direction horizontal \
    -width $pmesh_bot_str_width                                   \
    -spacing $pmesh_bot_str_intraset_spacing                      \
    -set_to_set_distance $pmesh_bot_str_interset_pitch            \
    -max_same_layer_jog_length $pmesh_bot_str_pitch               \
    -padcore_ring_bottom_layer_limit $pmesh_bot                   \
    -padcore_ring_top_layer_limit $pmesh_top                      \
    -start [expr $pmesh_bot_str_pitch]                            \
    -extend_to design_boundary

# VDD_SW - Don't creat pins
# Don't extend VDD_SW to boundary
addStripe -nets $sw_power_nets -layer $pmesh_bot -direction horizontal \
    -width $pmesh_bot_str_width                                   \
    -spacing $pmesh_bot_str_intraset_spacing                      \
    -set_to_set_distance $pmesh_bot_str_interset_pitch            \
    -max_same_layer_jog_length $pmesh_bot_str_pitch               \
    -padcore_ring_bottom_layer_limit $pmesh_bot                   \
    -padcore_ring_top_layer_limit $pmesh_top                      \
    -start [expr $pmesh_bot_str_pitch + ($pmesh_bot_str_intraset_spacing + $pmesh_bot_str_width)*2] \
    -create_pins 0

} else {
   setAddStripeMode -stacked_via_bottom_layer 3 \
                 -stacked_via_top_layer    $pmesh_top


# Add the stripes
#
# Use -start to offset the stripes slightly away from the core edge.
# Allow same-layer jogs to connect stripes to the core ring if some
# blockage is in the way (e.g., connections from core ring to pads).
# Restrict any routing around blockages to use only layers for power.

addStripe -nets $power_nets -layer $pmesh_bot -direction horizontal \
    -width $pmesh_bot_str_width                                   \
    -spacing $pmesh_bot_str_intraset_spacing                      \
    -set_to_set_distance $pmesh_bot_str_interset_pitch            \
    -max_same_layer_jog_length $pmesh_bot_str_pitch               \
    -padcore_ring_bottom_layer_limit $pmesh_bot                   \
    -padcore_ring_top_layer_limit $pmesh_top                      \
    -start [expr $pmesh_bot_str_pitch]                            \
    -extend_to design_boundary
}

if $::env(PWR_AWARE) {
sroute -allowJogging 0 -allowLayerChange 0 -connect  {secondaryPowerPin} -secondaryPinNet VDD -powerDomains TOP
}
