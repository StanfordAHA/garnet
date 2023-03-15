#=========================================================================
# phy-stripes.tcl
#=========================================================================
# Add horizontal M8 power stripes to right and left of phy block.
#
# Author : S. Richardson
# Date   : January, 2021

#-------------------------------------------------------------------------
# Find the phy
#-------------------------------------------------------------------------

set iphy [dbGet -p top.insts.name iphy]

set iphy_left   [dbGet $iphy.box_llx] ; # 1703.075
set iphy_right  [dbGet $iphy.box_urx] ; # 2853.095
set iphy_bottom [dbGet $iphy.box_lly] ; # 4798.416
set iphy_top    [dbGet $iphy.box_ury] ; # 4098.000

# E.g. { 99.99 4098.0  1703.075 4798.416 }
set iphy_stripe_area_left "\
    [dbGet top.fPlan.coreBox_llx] $iphy_bottom \
    $iphy_left $iphy_top"

# E.g. { 2853.095 4098.0  4800.0 4798.416 }
set iphy_stripe_area_right "\
    $iphy_right $iphy_bottom \
    [dbGet top.fPlan.coreBox_ury] $iphy_top"

#-------------------------------------------------------------------------
# Find phy pins that will connect to stripes
#-------------------------------------------------------------------------

proc phy_power_stripe_pins { net layer left_or_right } {

    # Return a list of the requested phy power pins. Example:
    #   set vdd_left [phy_power_stripe_pins DVDD M8 left]
    #   set first_pin_lly [dbGet [lindex $dvdd_left 1].rect_lly]

    # Assume that all M8 pins flush with left or right edge are power pins for stripes

    set iphy [dbGet -p top.insts.name iphy]
    set iphy_left_edge 0
    set iphy_right_edge [dbGet $iphy.box_sizex]

    set rlist { }
    set terms [dbGet -p $iphy.cell.pgTerms.name $net]
    foreach a [dbGet $terms.pins.allShapes] {
        set llx [dbGet $a.shapes.rect_llx]
        set urx [dbGet $a.shapes.rect_urx]
        # Must be on proper edge
        if { ($left_or_right == "left" ) && ($llx != $iphy_left_edge ) } { continue }
        if { ($left_or_right == "right") && ($urx != $iphy_right_edge) } { continue }
        # Must be on proper layer
        if { [dbGet $a.layer.name] != $layer } { 
            echo "WARNING phy ${left_or_right} edge ${net} pin not on layer ${layer}"
            continue
        }
        # Expect 2u high, but not strictly required.
        set height [dbGet $a.shapes.rect_sizey]
        if { $height != 2.0 } {
            echo "WARNING expected phy power stripe height 2.0, instead found" $height
        }
        # Join the list!
        lappend rlist $a.shapes
  }
  return $rlist
}

#-------------------------------------------------------------------------
# Build M8 stripes from left edge of core to left edge of phy block
#-------------------------------------------------------------------------

# 1. Make a list of M8 DVDD/DVSS pins on left edge of phy block.

set pwr_pins_left [phy_power_stripe_pins DVDD M8 left]
set gnd_pins_left [phy_power_stripe_pins DVSS M8 left]
set pg_pins_left "VDD $pwr_pins_left VSS $gnd_pins_left"

# 2. Build...the stripies on the left hand side

foreach p $pg_pins_left {

    # Sort pins according to pwr or gnd

    if { $p == "VDD" } { set net $p; continue }
    if { $p == "VSS" } { set net $p; continue }

    # Left edge of stripe aligns with left edge of core

    set llx [dbGet top.fPlan.coreBox_llx] ;             # x = 99.99
    set lly [expr $iphy_bottom + [dbGet $p.rect_lly]] ; # y = 4101 ish

    # Right edge of stripe aligns with right edge of pin
    # Originally, stripes overlapped phy by 19.999u...not sure why...
    # I changed it to overlap *only* the pin itself, hope that's okay.

    # set urx [expr [dbGet $iphy.box_llx] + 19.999]              ; # x=1723.074 (old)
    set urx [expr [dbGet $iphy.box_llx] + [dbGet $p.rect_sizey]] ; # x=1705.075 (new)
    set ury [expr $iphy_bottom + [dbGet $p.rect_ury]]            ; # y=4000 to 4900 ish

    # Build the stripe as a path, to match what addStripe used to do

    set rectangle [list $llx $lly  $urx $ury]
    set y [expr ($ury + $lly) / 2]
    set path "$llx $y $urx $y"
    set height [dbGet $p.rect_sizey]
    add_shape -net $net -status ROUTED -pathSeg $path \
        -layer M8 -shape STRIPE -width $height
}

#-------------------------------------------------------------------------
# Build M8 stripes from right edge of phy block to right edge of core
#-------------------------------------------------------------------------

# 1. Make a list of M8 DVDD/DVSS pins on right edge of phy block.

set pwr_pins_right [phy_power_stripe_pins DVDD M8 right]
set gnd_pins_right [phy_power_stripe_pins DVSS M8 right]
set pg_pins_right "VDD $pwr_pins_right VSS $gnd_pins_right"

# 2. Build...the stripies on the right hand side

foreach p $pg_pins_right {

    # Sort pins according to pwr or gnd

    if { $p == "VDD" } { set net $p; continue }
    if { $p == "VSS" } { set net $p; continue }

    # Left edge of stripe aligns with left edge of pin
    # Originally, stripes overlapped phy by 19.999u...not sure why...
    # I changed it to overlap *only* the pin itself, hope that's okay.

    # set llx [expr [dbGet $iphy.box_urx] - 19.999]              ; # x=2833.096 (old)
    set llx [expr [dbGet $iphy.box_urx] - [dbGet $p.rect_sizey]] ; # x=2851.095 (new)
    set lly [expr $iphy_bottom + [dbGet $p.rect_lly]]            ; # y=4000 to 4900 ish
    
    # Right edge of stripe aligns with right edge of core

    set urx [dbGet top.fPlan.coreBox_urx]             ; # x=
    set ury [expr $iphy_bottom + [dbGet $p.rect_ury]] ; #  y=4000 to 4900 ish

    set rectangle [list $llx $lly  $urx $ury]
    set y [expr ($ury + $lly) / 2]
    set path "$llx $y $urx $y"
    add_shape -net $net -status ROUTED -pathSeg $path \
        -layer M8 -shape STRIPE -width $height
}

#-------------------------------------------------------------------------
# Useful scripts for debug and development
#-------------------------------------------------------------------------

proc mySelectStripes { area } {
    # For debugging; select all M8 power/gnd stripes in the given area
    # Example: mySelectStripes $iphy_stripe_area_right
    set llx [expr [lindex $area 0] - 40]
    set lly [expr [lindex $area 1] - 40]
    set urx [expr [lindex $area 2] + 40]
    set ury [expr [lindex $area 3] + 40]

    set area "$llx $lly $urx $ury"
    editSelect -shape STRIPE -direction H -net { VSS VDD } -layer M8 -area $area
}
# mySelectStripes $iphy_stripe_area_right

proc test_phy_power_stripe_pins { } {

    # Tests for phy_power_stripe function

    foreach p [phy_power_stripe_pins DVDD M8 left] { echo vdd_left_rect=[dbGet $p.rect] }
    #    ...
    #    vdd_left_rect={0.0 27.96 2.0 29.96}
    #    vdd_left_rect={0.0 15.96 2.0 17.96}
    #    vdd_left_rect={0.0 3.96 2.0 5.96}

    foreach p [phy_power_stripe_pins DVSS M8 left] { echo vdd_left_rect=[dbGet $p.rect] }
    #    ...
    #    vdd_left_rect={0.0 30.96 2.0 32.96}
    #    vdd_left_rect={0.0 18.96 2.0 20.96}
    #    vdd_left_rect={0.0 6.96 2.0 8.96}

    foreach p [phy_power_stripe_pins DVDD M8 right] { echo vdd_right_rect=[dbGet $p.rect] }
    #    ...
    #    vdd_right_rect={1148.02 27.96 1150.02 29.96}
    #    vdd_right_rect={1148.02 15.96 1150.02 17.96}
    #    vdd_right_rect={1148.02 3.96 1150.02 5.96}

    foreach p [phy_power_stripe_pins DVSS M8 right] { echo vdd_right_rect=[dbGet $p.rect] }
    #    ...
    #    vdd_right_rect={1148.02 30.96 1150.02 32.96}
    #    vdd_right_rect={1148.02 18.96 1150.02 20.96}
    #    vdd_right_rect={1148.02 6.96 1150.02 8.96}
}

proc debug_phy_stripes {} {
    ########################################################################
    # A useful development tool.
    # Compare existing phy stripes (built using addStripes) to new ones.
    
    ##############################################################################
    # TESTING LEFT
    
    # Select old stripes
    deselectAll; mySelectStripes $iphy_stripe_area_left
    
    # Save stripes property info
    foreach stripe [dbGet selected] {
        set filename "tmp-[dbGet $stripe.box_lly]"
        echo "$filename-1"
        dbGet $stripe.?? > "$filename-1"
    }
    tail "$filename-1"
    
    # Delete old stripes
    deleteSelectedFromFPlan
    
    # Build new stripes (cut'n'paste new code from above)

    # Select new stripes
    deselectAll; select_stripes_left
    
    # Compare to old stripes
    foreach stripe [dbGet selected] {
        set filename "tmp-[dbGet $stripe.box_lly]"
        dbGet $stripe.?? > "$filename-2"
        echo  "diff $filename-1 $filename-2"
        catch "diff $filename-1 $filename-2 | grep box_urx"
    }

    ########################################################################
    # TESTING RIGHT
    
    # Select old stripes
    deselectAll; mySelectStripes $iphy_stripe_area_right
    
    # Save stripes property info
    foreach stripe [dbGet selected] {
        set filename "tmp-[dbGet $stripe.box_lly]"
        echo "$filename-1"
        dbGet $stripe.?? > "$filename-1"
    }
    tail "$filename-1"
    
    # Delete old stripes
    deleteSelectedFromFPlan
    
    # Build new stripes (cut'n'paste new code from above)
    
    # Select new stripes
    deselectAll; select_stripes_right
    
    # Compare to old stripes
    foreach stripe [dbGet selected] {
        set filename "tmp-[dbGet $stripe.box_lly]"
        dbGet $stripe.?? > "$filename-2"
        echo  "diff $filename-1 $filename-2"
        catch "diff $filename-1 $filename-2 | grep box:"
    }
}
