


#------------------------------------------------------------------------
# Add power switches for power aware flow
# ------------------------------------------------------------------------

# Choose the power switch name for this technology
set switch_name $ADK_POWER_SWITCH

set switch_width [dbGet [dbGetCellByName $switch_name].size_x]

# Pitch is a multiple of the M3 VDD stripe pitch 
set horiz_switch_pitch [expr $stripes_per_switch * $M3_str_interset_pitch]

# Don't add core_llx because addPowerSwitch command calculates
# Edge offset from edge of core area, and tap_edge_offset is from
# edge of cell area
set pwr_switch_edge_offset [expr $M3_str_offset + (2 * $M3_str_intraset_spacing + $M3_str_width) - ($switch_width / 3) + $horiz_switch_pitch]

# Add power switches in TOP domain
# Checker board pattern so switches are placed
# every alternate rows per column of switches
# The last power switch of the nth column
# is connected to 1st power switch of the
# (n+1)th column
# Avoid overlap with fixed std cells like
# boundary and tap cells
addPowerSwitch -column -powerDomain TOP \
     -leftOffset $pwr_switch_edge_offset\
     -horizontalPitch $horiz_switch_pitch   \
     -checkerBoard   \
     -loopBackAtEnd  \
     -enableNetOut PSenableNetOut\
     -noFixedStdCellOverlap  \
     -globalSwitchCellName $switch_name



