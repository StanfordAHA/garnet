#------------------------------------------------------------------------
# Add power switches for power aware flow
# ------------------------------------------------------------------------

# Set env var WHICH_SOC=amber for amber build, else uses default settings
set WHICH_SOC "default"
if { [info exists ::env(WHICH_SOC)] } { set WHICH_SOC $::env(WHICH_SOC) }

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

#-----------------------------------------------------------------------------
# Check that well taps exist between AON region and right/left chip boundaries
#-----------------------------------------------------------------------------

puts "--- Check well taps"

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
set AON_right_edge [lindex $AON_box 2]

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
  puts "Save design for later debugging..."
  saveDesign checkpoints/design.checkpoint/save.enc -user_path
  exit 13
}

if { [ dbGet top.name ] == "Tile_MemCore" && $WHICH_SOC == "amber" } {
  #-----------------------------------------------------------------------------
  # Check that well taps (i.e. well-tap power-switch combos) exist between SRAMs
  #-----------------------------------------------------------------------------

  puts "\nChecking to see that well taps exist in space between SRAMs\n"

  # Find the srams
  set sram_collection [get_cells -quiet -hier -filter {is_memory_cell==true}]
  foreach_in_collection s $sram_collection {
      selectInst $s
      set srams [dbget selected]
  }
  foreach n [dbget $srams.name] { puts "Found sram $n" }

  # Verify that there are exactly two srams
  set n_srams [ llength $srams.box ]
  if { $n_srams != 2 } {
     puts "WARNING found $n_srams SRAMs, should have been two"
     puts "WARNING correctness check is sus"
  }

  # Make a sorted list of sram x-coordinate edges
  set xlist "[ dbget $srams.box_llx ] [ dbget $srams.box_urx ]"
  set sorted_exes [ lsort -real $xlist ]
  # 61.02 102.155 129.155 170.29

  # Find left and right edges of the gap between SRAMs
  set left_edge_of_gap  [ lindex $sorted_exes 1 ]
  set right_edge_of_gap [ lindex $sorted_exes 2 ]

  # No check if no gap
  if { $left_edge_of_gap == $right_edge_of_gap } {
     puts "tiles are abutted, no check needed"

  } else {

    # See if well taps (power switches) exist between the gaps
    # And yes we need to check both edges of power switch!!

    # Make a list of llx for each power switch (again) (why not)
    set ps_llx_list [ dbget [ dbget -p2 top.insts.cell.name $tap_cell ].box_llx ]

    # Find width of power switch; must be fully in the gap!
    set ps_width [ dbget [ dbget -p2 top.insts.cell.name $tap_cell ].box_sizex ]
    set ps_width [ lindex $ps_width 0 ]

    # Verify that at least one welltap column exists fully in the gap
    set found_valid_ps false
    foreach llx $ps_llx_list {
      set urx [ expr $llx + $ps_width ]
      set cond1 false; set cond2 false
      if { $llx > $left_edge_of_gap  } { set cond1 true }
      if { $urx < $right_edge_of_gap } { set cond2 true }
      if { $cond1 && $cond2 } {
        puts "Found valid power-switch column at llx=$llx"
        set found_valid_ps true
        break
      }  
    }

    if { $found_valid_ps } {
      puts "Oll Korrect -- found well taps in between the two SRAMs"
    } else {
      puts "ERROR Cannot find power-switches between the SRAMS, thus no well taps there"
      puts "Saving design for later debugging..."
      saveDesign checkpoints/design.checkpoint/save.enc -user_path
      exit 13
    }
  }
}
