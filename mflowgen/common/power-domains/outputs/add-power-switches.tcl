


#------------------------------------------------------------------------
# Add power switches for power aware flow
# ------------------------------------------------------------------------

# Choose the switch name
set switch_name "SC7P5T2V_HEADERBUFX8_SSC14R"

# Use GF HEADERBUF

# Add power switches in TOP domain
# Checker board pattern so switches are placed
# every alternate rows per column of switches
# The last power switch of the nth column
# is connected to 1st power switch of the
# (n+1)th column
# Avoid overlap with fixed std cells like
# boundary and tap cells
addPowerSwitch -column -powerDomain TOP \
     -leftOffset $left_offset\
     -horizontalPitch $horiz_pitch   \
     -checkerBoard   \
     -loopBackAtEnd  \
     -enableNetOut PSenableNetOut\
     -noFixedStdCellOverlap  \
     -globalSwitchCellName $switch_name



