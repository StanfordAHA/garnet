#========================================================================
# mem-pd-params.tcl
#========================================================================
# Author: Alex Carsello
# Date: 3/7/21


# Boundary AON TAP params

# AON boundary taps must line up with M3 VDD stripes.
# 'stripes_per_tap' controls the space between AON taps
# as a multiple of the M3 power stripe pitch.
set stripes_per_tap 18


# Power switch params

# Like the taps, power switches must line up with M3 VDD stripes.
# 'stripes_per switch' controls space betwen power switches as a
# multiple of the M3 power stripe pitch.
# 
# sps12 (original default) yields 14 columns of switches and 4.5 hr runtime
# sps26 yields six columns and finishes in 2.5 hr
set stripes_per_switch 26

# AON box floorplanning params

# Sets width of AON region as a multiple of the unit stdcell width.
set aon_width 160

# Sets height of AON region as a multiple of the unit stdcell height.
# This should always be an even number so that the
# AON region can start an end on an even-numbered row.
set aon_height 24

# Sets AON box horizontal offset from center in # of unit stdcell widths.
# We want to move this to the right of the SRAM macros for mem tile.
# ---
# RESOLVEME - SR: I moved it back to the left b/c runtime was slightly faster.
# Does this matter? I can move it back.
# ---
set aon_horiz_offset -80

# Sets AON box vertical offset from center in # of unit stdcell heights.
set aon_vert_offset 15
