#========================================================================
# mem-pd-params.tcl
#========================================================================
# Author: Alex Carsello
# Date: 3/7/21


# Boundary AON TAP Params

# AON boundary taps must line up with M3 VDD stripes.
# stripes_per_tap controls the space between AON taps
# as a multiple of the M3 power stripe pitch
set stripes_per_tap 12


# Power Switch Params

# Like the taps, power switches must also line up
# with M3 VDD stripes. stripes_per switch controls 
# space betwen power switches as a multiple of the M3
# power stripe pitch.

# Original mtile had six columns of power switches.
# New default balue 12 yields fourteen columns.
# Let's try increasing 12=>26, see what happens
# set stripes_per_switch 12
set stripes_per_switch 26


# AON box floorplanning params

# Sets width of AON region as a multiple of the 
# unit stdcell width
# set aon_width 160

# Original box was skinnier, let's try 100 and see what happens
set aon_width 110



# Sets height of AON region as a multiple of the
# unit stdcell height.
# This should always be an even number so that the
# AON region can start an end on an even-numbered row.
set aon_height 24

# Sets AON box horizontal offset from center
# We went to move this to the right of the SRAM macros for mem tile.
# set aon_horiz_offset 80

# Can this be negative? I guess we'll find out!
# Hoping -80 will bring it back to where it was before
set aon_horiz_offset -80



# Sets AON box vertical offset from center
# set aon_vert_offset 15

# Original position was higher than 15, let's try 30 see how that goes
set aon_vert_offset 30
