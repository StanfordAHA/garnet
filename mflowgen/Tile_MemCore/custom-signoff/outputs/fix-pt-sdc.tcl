#=========================================================================
# fix-pt-sdc.tcl
#=========================================================================
# Sourced by the signoff step right after generate-results.tcl (lake-spec
# builds). Makes the SDC that writeTimingCon wrote for PrimeTime readable by
# PrimeTime's read_sdc, which accepts SDC commands only.
#
# writeTimingCon splits a long object list into
#     set __coll_N [get_ports {...}]
#     append_to_collection __coll_N [get_ports {...}]
# and append_to_collection is not an SDC command: read_sdc stops at the first
# one (CMD-005, "Errors reading SDC file") and drops every constraint after
# it. Every consumer of design.pt.sdc (PT signoff, genlibdb, PnR-level
# memtile power) hit this on fw4_dw16_sc4096_sp_in2_out2_vc2 (2026-10-07):
# reading stopped at line 4283 (a 442-port SB collection), and among the
# lost constraints was the 2-cycle config_config_addr -> read_config_data
# multicycle, so PT timed that path as single-cycle (-1229 ps).
#
# Each such collection is folded back into its `set` line (all appends
# with the same get_* command, collection not referenced in between);
# anything else is left as is and counted. The original file is kept as
# <design>.pt.sdc.orig.

proc fix_pt_sdc {path} {
  set fh [open $path r]
  set lines [split [read -nonewline $fh] "\n"]
  close $fh

  set set_re {^set (__coll_[0-9]+) \[(get_[a-z_]+) \{(.*)\}\]\s*$}
  set app_re {^append_to_collection (__coll_[0-9]+) \[(get_[a-z_]+) \{(.*)\}\]\s*$}
  array set first {}
  array set apps {}
  set i 0
  foreach l $lines {
    if {[regexp $set_re $l -> v t items]} {
      set first($v) [list $i $t $items]
    } elseif {[regexp $app_re $l -> v t items]} {
      lappend apps($v) [list $i $t $items]
    }
    incr i
  }

  set merged 0
  set drop {}
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
  set i 0
  set left 0
  set drop [lsort -integer $drop]
  set d 0
  foreach l $lines {
    if {$d < [llength $drop] && [lindex $drop $d] == $i} {
      incr d
    } else {
      lappend out $l
      if {[string match "append_to_collection *" $l]} { incr left }
    }
    incr i
  }
  if {$merged} {
    file copy -force $path $path.orig
    set fh [open $path w]
    puts $fh [join $out "\n"]
    close $fh
  }
  return [list $merged $left]
}

lassign [fix_pt_sdc $vars(results_dir)/$vars(design).pt.sdc] ptsdc_merged ptsdc_left
puts "INFO: fix-pt-sdc: folded $ptsdc_merged append_to_collection lines into their\
      collections; $ptsdc_left left (read_sdc stops at the first)"
