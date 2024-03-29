#========================================================================
# mem-pd-params.tcl
#========================================================================
# Author: Alex Carsello
# Date: 3/7/21

# Set env var WHICH_SOC=amber for amber build, else uses default settings
set WHICH_SOC "default"
if { [info exists ::env(WHICH_SOC)] } { set WHICH_SOC $::env(WHICH_SOC) }

# VDD stripe sparsity params

# Always-on domain is much smaller than the switching domain, so need
# fewer VDD AON power stripes vs. VDD_SW switching-domain stripes.
# Sparsity parm controls VDD stripe sparsity for M3 power stripes;
# sparsity 3 means one VDD stripe for every three VDD_SW stripes etc.
set vdd_m3_stripe_sparsity 1
if { $WHICH_SOC == "amber" } { set vdd_m3_stripe_sparsity 2 }


# Allow SDF registers?

# If sparsity > 1, should be able to use SDF registers; otherwise this
# should be false because the M3 stripe density makes SDF routing too
# difficult (there is a garnet issue about this).
set adk_allow_sdf_regs true


# Boundary AON TAP params

# AON boundary taps must line up with M3 VDD stripes.
# 'stripes_per_tap' controls the space between AON taps
# as a multiple of the M3 power stripe pitch.
set stripes_per_tap 9
if { $WHICH_SOC == "amber" } { set stripes_per_tap 22 }

# Note that 'stripes_per_tap' must be a multiple of vdd sparsity.
# This integer-div followed by integer-mul corrects that situation.
# Example:
#   WARNING 1/3 you wanted one VDD tap for every 9 stripe-groups
#   WARNING 2/3 but only one group out of every 2 has a VDD stripe
#   WARNING 3/3 correcting 'stripes_per_tap' parm from 9 to 8
# 
set vdd_stripes_per_tap [ expr $stripes_per_tap / $vdd_m3_stripe_sparsity ]
set corrected_stripes_per_tap [ expr $vdd_stripes_per_tap * $vdd_m3_stripe_sparsity ]
if { $stripes_per_tap != $corrected_stripes_per_tap } {
    puts "WARNING 1/3 you wanted one VDD tap for every $stripes_per_tap stripe-groups"
    puts "WARNING 2/3 but only one group out of every $vdd_m3_stripe_sparsity has a VDD stripe"
    puts "WARNING 3/3 correcting 'stripes_per_tap' parm from $stripes_per_tap to $corrected_stripes_per_tap"
    set stripes_per_tap $corrected_stripes_per_tap
}


# Power switch params

# Like the taps, power switches must line up with M3 VDD stripes.
# 'stripes_per switch' controls space betwen power switches as a
# multiple of the M3 power stripe pitch.
# 
# sps12 (original default) yields 14 columns of switches and 4.5 hr runtime
# sps26 yields six columns and finishes in 2.5 hr
set stripes_per_switch 14
if { $WHICH_SOC == "amber" } { set stripes_per_switch 22 }

# Note that 'stripes_per_switch' must be a multiple of vdd sparsity.
set vdd_stripes_per_switch [ expr $stripes_per_switch / $vdd_m3_stripe_sparsity ]
set stripes_per_switch [ expr $vdd_stripes_per_switch * $vdd_m3_stripe_sparsity ]


# AON box floorplanning params

# Sets width of AON region as a multiple of the unit stdcell width.
set aon_width 160

# Sets height of AON region as a multiple of the unit stdcell height.
# This should always be an even number so that the
# AON region can start an end on an even-numbered row.
set aon_height 26
if { $WHICH_SOC == "amber" } { set aon_height 24 }

# Sets AON box horizontal offset from center in # of unit stdcell widths.

# Negative offset puts AON left of center
# If stripes_per_tap is 22, aon_horiz_offset should be 84; 80 creates a dead zone see issue 923.
# FIXME aon placement should maybe be algorithmic based on distance from power switches etc.

set aon_horiz_offset 0
if { $WHICH_SOC == "amber" } { set aon_horiz_offset 90 }

# Sets AON box vertical offset from center in # of unit stdcell heights.
set aon_vert_offset 15
