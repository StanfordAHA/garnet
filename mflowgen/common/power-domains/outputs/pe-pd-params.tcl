#========================================================================
# pe-pd-params.tcl
#========================================================================
# Author: Alex Carsello
# Date: 3/7/21

# VDD stripe sparsity params

# Always-on domain is much smaller than the switching domain, so need
# fewer VDD AON power stripes vs. VDD_SW switching-domain stripes.
# Sparsity parm controls VDD stripe sparsity for M3 power stripes;
# sparsity 3 means one VDD stripe for every three VDD_SW stripes etc.
set vdd_m3_stripe_sparsity 3


# Allow SDF registers?

# If sparsity > 1, should be able to use SDF registers; otherwise this
# should be false because the M3 stripe density makes SDF routing too
# difficult (there is a garnet issue about this).
set adk_allow_sdf_regs true


# Boundary AON TAP params

# AON boundary taps must line up with M3 VDD stripes.
# 'stripes_per_tap' controls the space between AON taps
# as a multiple of the M3 power stripe pitch.
set stripes_per_tap 18

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
# If set to 12 in Amber (TSMC) design, get five columns of switches.
# If set to 18, get 3 cols symmetrically placed, center col at center chip.
set stripes_per_switch 18

# Note that 'stripes_per_switch' must be a multiple of vdd sparsity.
set vdd_stripes_per_switch [ expr $stripes_per_switch / $vdd_m3_stripe_sparsity ]
set stripes_per_switch [ expr $vdd_stripes_per_switch * $vdd_m3_stripe_sparsity ]


# AON box floorplanning params

# Sets width of AON region as a multiple of the unit stdcell width.
set aon_width 160

# Sets height of AON region as a multiple of the unit stdcell height.
# This should always be an even number so that the
# AON region can start an end on an even-numbered row.
set aon_height 24

# Sets AON box horizontal offset from center in # of unit stdcell widths.
set aon_horiz_offset 0

# Sets AON box vertical offset from center in # of unit stdcell heights.
set aon_vert_offset 30
