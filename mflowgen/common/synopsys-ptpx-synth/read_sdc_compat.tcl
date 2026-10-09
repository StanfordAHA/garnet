#=========================================================================
# read_sdc_compat.tcl
#=========================================================================
# PrimeTime's read_sdc accepts SDC commands only and stops at the first
# other command, silently dropping every constraint after it ("Errors
# reading SDC file"). Non-SDC lines that show up in the SDCs these steps read:
#
#  - `current_design <name>` -- Genus writes it near the top of its SDC
#    (read_sdc: CMD-012). On the 2026-10-07 garnet sweep smoke run the
#    standalone idle/active power read only 12 lines of lakespec's synth SDC
#    and ran with no clock at all (PWR-171).
#  - synthesis-only directives PT doesn't have (CMD-005): set_dont_use,
#    set_dont_touch, set_dont_touch_network, set_ideal_net, set_fix_hold
#    (measured on PT Q-2019.12-SP2). Genus writes `set_dont_use` after
#    set_driving_cell; on the 2026-10-08 smoke rerun it cut lakespec's SDC
#    before `set_load` on the outputs. Not "any command PT lacks": read_sdc
#    accepts set_logic_zero, set_max_dynamic_power, ... that `info commands`
#    doesn't list.
#  - `append_to_collection __coll_N [get_* {...}]` -- Innovus writeTimingCon
#    splits long object lists that way (CMD-005).
#
# read_sdc_compat writes <sdc>.compat.sdc with the first two dropped (with any
# backslash continuation lines) and the last folded into their `set __coll_N`
# line (the folding of garnet's Tile_MemCore custom-signoff/outputs/
# fix-pt-sdc.tcl), then read_sdc's it.
# Same file as lake pd/thesis/synopsys-ptpx-{synth,gl}/read_sdc_compat.tcl
# (33eae24e); copies in garnet's synopsys-ptpx-{synth,gl,rtl}/ (mflowgen copies
# one node directory per step): keep them identical. In garnet, Genus's synth
# SDC stopped tile synth-level power (post-synth-power, memtile-power-synth-*)
# at `current_design Tile_*`: no clock.

proc read_sdc_compat {path} {
  set fh [open $path r]
  set lines [split [read -nonewline $fh] "\n"]
  close $fh

  set drop_re {^\s*(current_design|set_dont_use|set_dont_touch|set_dont_touch_network|set_ideal_net|set_fix_hold)\s}
  set set_re {^set (__coll_[0-9]+) \[(get_[a-z_]+) \{(.*)\}\]\s*$}
  set app_re {^append_to_collection (__coll_[0-9]+) \[(get_[a-z_]+) \{(.*)\}\]\s*$}
  array set first {}
  array set apps {}
  array set dropped {}
  set drop {}
  set i 0
  set cont 0
  foreach l $lines {
    if {$cont} {
      # continuation (trailing backslash) of a dropped command goes with it
      lappend drop $i
    } elseif {[regexp $drop_re $l -> cmd]} {
      lappend drop $i
      if {![info exists dropped($cmd)]} { set dropped($cmd) 0 }
      incr dropped($cmd)
    } elseif {[regexp $set_re $l -> v t items]} {
      set first($v) [list $i $t $items]
    } elseif {[regexp $app_re $l -> v t items]} {
      lappend apps($v) [list $i $t $items]
    }
    set cont [expr {[llength $drop] && [lindex $drop end] == $i && [regexp {\\\s*$} $l]}]
    incr i
  }

  set merged 0
  foreach v [array names apps] {
    if {![info exists first($v)]} { continue }
    lassign $first($v) fi ft all
    set ok 1
    set last $fi
    foreach a $apps($v) {
      lassign $a ai at items
      if {$ai < $fi || $at ne $ft} { set ok 0; break }
      append all " " $items
      if {$ai > $last} { set last $ai }
    }
    # The merged set must not change what a use between the lines would see.
    for {set k [expr {$fi + 1}]} {$ok && $k < $last} {incr k} {
      if {[string first "\$$v" [lindex $lines $k]] >= 0} { set ok 0 }
    }
    if {!$ok} { continue }
    lset lines $fi "set $v \[$ft \{$all\}\]"
    foreach a $apps($v) { lappend drop [lindex $a 0] }
    incr merged [llength $apps($v)]
  }

  set out {}
  set left 0
  set drop [lsort -integer $drop]
  set d 0
  set i 0
  foreach l $lines {
    if {$d < [llength $drop] && [lindex $drop $d] == $i} {
      incr d
    } else {
      lappend out $l
      if {[string match "append_to_collection *" $l]} { incr left }
    }
    incr i
  }
  set compat [file rootname [file tail $path]].compat.sdc
  set fh [open $compat w]
  puts $fh [join $out "\n"]
  close $fh
  set what {}
  foreach c [lsort [array names dropped]] { lappend what "$dropped($c) $c" }
  if {![llength $what]} { set what {nothing} }
  puts "INFO: read_sdc_compat: $path -> $compat: dropped [join $what {, }];\
        folded $merged append_to_collection ($left left; read_sdc stops at the first)"
  return [read_sdc -echo $compat]
}
