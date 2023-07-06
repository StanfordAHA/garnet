#=========================================================================
# pin-assignments.tcl
#=========================================================================

#-------------------------------------------------------------------------
# Pin Assignments
#-------------------------------------------------------------------------

# Take all ports and split into halves

set all_ports    [dbGet top.terms.name]
set num_ports    [llength $all_ports]
set ports_idx_q1 [expr $num_ports / 4]
set ports_idx_q2 [expr $ports_idx_q1 * 2]
set ports_idx_q3 [expr $ports_idx_q1 * 3]

set pins_left   [lrange $all_ports 0             [expr $ports_idx_q1 - 1]]
set pins_right  [lrange $all_ports $ports_idx_q1 [expr $ports_idx_q2 - 1]]
set pins_top    [lrange $all_ports $ports_idx_q2 [expr $ports_idx_q3 - 1]]
set pins_bottom [lrange $all_ports $ports_idx_q3 [expr $num_ports - 1]]

# create a function to set the layer of the pins
proc spread_pins_avoid_stripes {side pin_list pins_per_slot {slot_offset 0}} {
  global ADK_M3_TO_M8_STRIPE_WIDTH_LIST
  global ADK_M3_TO_M8_STRIPE_OFSET_LIST
  global ADK_M3_TO_M8_STRIPE_SPACE_LIST
  set fplan_width [dbGet top.fPlan.box_urx]
  set fplan_height [dbGet top.fPlan.box_ury]
  set num_pins [llength $pin_list]
  set num_slots [expr ceil($num_pins / $pins_per_slot)]
  # decide the pin parameters based on side
  if { $side == "TOP" || $side == "BOTTOM" } {
    set pin_layer m5
    set adk_stripe_width [lindex $ADK_M3_TO_M8_STRIPE_WIDTH_LIST 2]
    set adk_stripe_ofset [lindex $ADK_M3_TO_M8_STRIPE_OFSET_LIST 2]
    set adk_stripe_space [lindex $ADK_M3_TO_M8_STRIPE_SPACE_LIST 2]
  } elseif { $side == "LEFT" || $side == "RIGHT" } {
    set pin_layer m6
    set adk_stripe_width [lindex $ADK_M3_TO_M8_STRIPE_WIDTH_LIST 3]
    set adk_stripe_ofset [lindex $ADK_M3_TO_M8_STRIPE_OFSET_LIST 3]
    set adk_stripe_space [lindex $ADK_M3_TO_M8_STRIPE_SPACE_LIST 3]
  } else {
    puts "Not a valid side. Please choose from LEFT, RIGHT, TOP, or BOTTOM."
    return
  }
  set stripe_space [expr $adk_stripe_width + $adk_stripe_space]
  set pin_space [expr $stripe_space / ($pins_per_slot + 1)]
  set first_stripe_ofset [expr $adk_stripe_ofset + ($adk_stripe_width / 2)]
  setPinAssignMode -pinEditInBatch true
  # loop through num_slots
  for {set s 0} {$s < $num_slots} {incr s} {
    for {set p 0} {$p < $pins_per_slot} {incr p} {
      # pin name
      set pin_index [expr $s * $pins_per_slot + $p]
      set pin_name [lindex $pin_list $pin_index]
      set offset [expr $first_stripe_ofset + ($s + $slot_offset) * $stripe_space]
      # pin location
      if { $side == "TOP" } {
        set pin_x [expr $offset + ($p + 1) * $pin_space]
        set pin_y $fplan_height
      } elseif { $side == "BOTTOM" } {
        set pin_x [expr $offset + ($p + 1) * $pin_space]
        set pin_y 0
      } elseif { $side == "LEFT" } {
        set pin_x 0
        set pin_y [expr $offset + ($p + 1) * $pin_space]
      } elseif { $side == "RIGHT" } {
        set pin_x $fplan_width
        set pin_y [expr $offset + ($p + 1) * $pin_space]
      }
      # assign the pin
      editPin \
          -layer $pin_layer \
          -pin $pin_name \
          -side $side \
          -assign [list $pin_x $pin_y]
    }
  }
  setPinAssignMode -pinEditInBatch false
}

spread_pins_avoid_stripes "LEFT"   $pins_left   3 8
spread_pins_avoid_stripes "RIGHT"  $pins_right  3 8
spread_pins_avoid_stripes "TOP"    $pins_top    1 8
spread_pins_avoid_stripes "BOTTOM" $pins_bottom 1 8
