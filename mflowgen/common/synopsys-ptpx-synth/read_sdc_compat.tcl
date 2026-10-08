#=========================================================================
# read_sdc_compat.tcl
#=========================================================================
# PrimeTime's read_sdc accepts SDC commands only and stops at the first
# other command, silently dropping every constraint after it ("Errors
# reading SDC file"). Two non-SDC lines show up in the SDCs these steps read:
#
#  - `current_design <name>` -- Genus writes it near the top of its SDC
#    (read_sdc: CMD-012). On the 2026-10-07 garnet sweep smoke run the
#    standalone idle/active power read only 12 lines of lakespec's synth SDC
#    and ran with no clock at all (PWR-171).
#  - `append_to_collection __coll_N [get_* {...}]` -- Innovus writeTimingCon
#    splits long object lists that way (CMD-005).
#
# read_sdc_compat writes <sdc>.compat.sdc with the former dropped and the
# latter folded into their `set __coll_N` line (the folding of garnet's
# Tile_MemCore custom-signoff/outputs/fix-pt-sdc.tcl), then read_sdc's it.
# Same file as lake pd/thesis/synopsys-ptpx-{synth,gl}/read_sdc_compat.tcl
# (33eae24e); copies in garnet's synopsys-ptpx-{synth,gl,rtl}/ (mflowgen copies
# one node directory per step): keep them identical. In garnet, Genus's synth
# SDC stopped tile synth-level power (post-synth-power, memtile-power-synth-*)
# at `current_design Tile_*`: no clock.

proc read_sdc_compat {path} {
  set fh [open $path r]
  set lines [split [read -nonewline $fh] "\n"]
  close $fh

  set set_re {^set (__coll_[0-9]+) \[(get_[a-z_]+) \{(.*)\}\]\s*$}
  set app_re {^append_to_collection (__coll_[0-9]+) \[(get_[a-z_]+) \{(.*)\}\]\s*$}
  array set first {}
  array set apps {}
  set drop {}
  set i 0
  foreach l $lines {
    if {[regexp {^\s*current_design\s+\S} $l]} {
      lappend drop $i
    } elseif {[regexp $set_re $l -> v t items]} {
      set first($v) [list $i $t $items]
    } elseif {[regexp $app_re $l -> v t items]} {
      lappend apps($v) [list $i $t $items]
    }
    incr i
  }
  set dropped_cd [llength $drop]

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
  puts "INFO: read_sdc_compat: $path -> $compat: dropped $dropped_cd current_design,\
        folded $merged append_to_collection ($left left; read_sdc stops at the first)"
  return [read_sdc -echo $compat]
}
