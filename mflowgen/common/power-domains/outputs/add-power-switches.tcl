


#------------------------------------------------------------------------
# Add power switches for power aware flow
# ------------------------------------------------------------------------

# Choose the switch name
set switch_name "HDR10XSICWDPDTD1BWP16P90"

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

#------------------------------------------------------------------------
# Check to make sure there well taps exist between AON region and
# right/left chip boundaries.
#------------------------------------------------------------------------

if {[info exists ADK_AON_TAP_CELL] && [expr {$ADK_AON_TAP_CELL ne ""}]} {
    set tap_cell $ADK_AON_TAP_CELL
} else {
    set tap_cell $ADK_POWER_SWITCH
}    

# Make a list of llx for each power switch
set ps_llx_list [ dbget [ dbget -p2 top.insts.cell.name $tap_cell ].box_llx ]

# Find AON box e.g. {33.75 51.84 48.15 65.664}
set AON_box [lindex [dbget [ dbget -p top.fPlan.groups.name AON ].boxes] 0]
set AON_box [ lindex $AON_box 0 ]

# Find x loc for left and right edges of AON box
set AON_left_edge [lindex $AON_box 0]
set AON_right_edge [lindex $AON_box 3]

# Set right and left props
set ps_to_right false
set ps_to_left false
foreach x $ps_llx_list {
  if { $x < $AON_left_edge  } { set ps_to_left  true }
  if { $x > $AON_right_edge } { set ps_to_right true }
}

if { $ps_to_left && $ps_to_right } {
  puts "Oll Korrect -- found well taps both right and left of AON region"
} else {
  puts "ERROR Missing power switches"
  if { $ps_to_left } { 
    puts "ERROR Found no power-switch taps to right of AON region"
  } else {
    puts "ERROR Found no power-switch taps to left of AON region"
  }
}



