#=========================================================================
# fix-tap-gaps.tcl
#=========================================================================
# Sourced right after the endcaps and well taps go in (lake-spec builds).
#
# GF12's smallest filler is 2 sites, and taps/endcaps are fixed, so a tap that
# lands exactly one site short of a fixed neighbor leaves a hole that nothing
# can fill or move: checkPlace flags it (SPFillerGapViolation) and route's
# `routeDesign -placementCheck` aborts with NRIG-76. Whether it happens depends
# on where a macro's halo edge falls against the tap grid, i.e. on die width --
# fw4_dw16_sc8192_dp_in4_out4_vc2 hit it in 116 rows (TAPX14 ending at
# x=437.388, the ROWCAPRX8 beside the second SRAM starting at 437.472) while its
# _rv twin, with a wider die, did not.
#
# Each such tap is moved one site away from the gap, widening it to 2 sites
# (FILLX2 fills it); if that would leave a 1-site gap or overlap on its other
# side, it moves toward the gap and abuts instead. No std cell is placed yet,
# so the tap only moves into ordinary placement area. Gaps are measured
# directly (not via checkPlace, whose filler-gap check depends on the
# place_detail_legalization_inst_gap mode the place step sets later).
# No-op when no tap has a 1-site gap.

set ftg_site [dbGet top.fPlan.coreSite.size_x]

# Sites from $tap to the nearest fixed cell on its left and right, capped at 3.
proc ftg_room {tap} {
  global ftg_site
  lassign [lindex [dbGet $tap.box] 0] llx lly urx ury
  set y [expr {($lly + $ury) / 2.0}]
  set box [list [expr {$llx - 3*$ftg_site}] [expr {$y - 0.01}] [expr {$urx + 3*$ftg_site}] [expr {$y + 0.01}]]
  set l 3
  set r 3
  foreach i [dbQuery -area $box -objType inst] {
    if {$i eq $tap || [dbGet $i.pStatus] ne "fixed"} continue
    lassign [lindex [dbGet $i.box] 0] ix0 iy0 ix1 iy1
    if {$ix1 <= $llx + 1e-6} { set l [expr {min($l, int(round(($llx - $ix1) / $ftg_site)))}] }
    if {$ix0 >= $urx - 1e-6} { set r [expr {min($r, int(round(($ix0 - $urx) / $ftg_site)))}] }
  }
  return [list $l $r]
}

set ftg_found 0
set ftg_moved 0
foreach tap [dbGet -e -p top.insts.name WELLTAP*] {
  if {[dbGet $tap.pStatus] ne "fixed"} continue
  lassign [ftg_room $tap] l r
  if {$l != 1 && $r != 1} continue
  incr ftg_found
  # Step away from the gap first (-1 = left); either side must end at 0 or >=2.
  set dirs [expr {$r == 1 ? "-1 1" : "1 -1"}]
  foreach dir $dirs {
    set nl [expr {$l + $dir}]
    set nr [expr {$r - $dir}]
    if {$nl < 0 || $nl == 1 || $nr < 0 || $nr == 1} continue
    lassign [lindex [dbGet $tap.box] 0] llx lly
    placeInstance [dbGet $tap.name] [expr {$llx + $dir * $ftg_site}] $lly [dbGet $tap.orient] -fixed
    incr ftg_moved
    break
  }
}
puts "INFO: fix-tap-gaps: $ftg_found well taps had a 1-site gap to a fixed cell;\
      moved $ftg_moved, [expr {$ftg_found - $ftg_moved}] left"
