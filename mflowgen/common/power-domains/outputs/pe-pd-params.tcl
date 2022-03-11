#========================================================================
# pe-pd-params.tcl
#========================================================================
# Author: Alex Carsello
# Date: 3/7/21


# Boundary AON TAP Params

# AON boundary taps must line up with M3 VDD stripes.
# stripes_per_tap controls the space between AON taps
# as a multiple of the M3 power stripe pitch
set stripes_per_tap 8


# Power Switch Params

# Like the taps, power switches must also line up
# with M3 VDD stripes. stripes_per switch controls 
# space betwen power switches as a multiple of the M3
# power stripe pitch.
set stripes_per_switch 8


# AON box floorplanning params

# Sets width of AON region as a multiple of the 
# unit stdcell width
set aon_width 160

# Sets height of AON region as a multiple of the
# unit stdcell height.
# This should always be an even number so that the
# AON region can start an end on an even-numbered row.
set aon_height 24

# Sets AON box horizontal offset from center in # of unit stdcell widths
set aon_horiz_offset 0

# Sets AON box vertical offset from center in # of unit std cell heights
set aon_vert_offset 15