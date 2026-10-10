#=========================================================================
# pg_diag.tcl -- read-only power-grid / DRC diagnosis of a signoff checkpoint
#=========================================================================
# Run by pg_diag.sh (innovus -files pg_diag.tcl) with
#   PG_DIAG_CKPT = <ws>/<N>-cadence-innovus-signoff/checkpoints/design.checkpoint/save.enc.dat
#   PG_DIAG_TOP  = design name (Tile_MemCore)
# from an empty output directory. It restores the checkpoint (self-contained:
# libs are copied inside save.enc.dat), writes text reports to the current
# directory and exits. It never saves the design, so the workspace is not
# touched; the via trials at the end only change the in-memory copy.
#
# Reports:
#   summary.txt     floorplan, rows, macros, layers, route blockages, PG wire/via inventory
#   opens.txt       every verifyConnectivity open with what lies in its box
#                   (special/regular wires, vias, std cells on it, blockages)
#   conn_*.rpt      verifyConnectivity reports (before / after each trial)
#   drc.rpt         verify_drc with a high limit; drc_summary.txt classifies it
#                   (wire vs Routing Blockage = edge/halo artifact, or real)
#   trials.txt      in-memory fixes tried and the opens / DRC they leave

proc out {fh args} { puts $fh [join $args " "]; flush $fh }

proc lname {l} { if {$l eq "" || $l eq "0x0"} { return "-" }; return [dbGet $l.name] }

# dbGet returns a box as a one-element list of {x1 y1 x2 y2}
proc bx {b} { if {[llength $b] == 1} { set b [lindex $b 0] }; return $b }

proc box_area {b} { lassign [bx $b] x1 y1 x2 y2; return [expr {($x2-$x1)*($y2-$y1)}] }

proc grow {b d} {
  lassign [bx $b] x1 y1 x2 y2
  return [list [expr {$x1-$d}] [expr {$y1-$d}] [expr {$x2+$d}] [expr {$y2+$d}]]
}

# dbQuery with fallbacks for older option spellings (-areas vs -area,
# -overlap_only absent): written on Innovus 23.1, run on 22.13.
proc q {box type {layer ""} {overlap 0}} {
  set extra {}
  if {$layer ne ""} { lappend extra -layers $layer }
  set ov [expr {$overlap ? "-overlap_only" : ""}]
  foreach form [list "-areas {[list [bx $box]]} $ov" "-areas {[list [bx $box]]}" "-area {[bx $box]}"] {
    if {![catch {eval dbQuery $form -objType $type $extra} r]} { return $r }
  }
  return {}
}

proc attr {o a {dflt ""}} { if {[catch {dbGet $o.$a} v]} { return $dflt }; return $v }

# Open markers of verifyConnectivity, as {message box} pairs.
proc conn_opens {} {
  set res {}
  foreach m [dbGet -e top.markers] {
    if {[dbGet $m.type] ne "Connectivity" || [dbGet $m.subType] ne "Open"} { continue }
    lappend res [list [dbGet $m.message] [bx [dbGet $m.box]]]
  }
  return $res
}

# Fallback when the markers can't be read: the report's
# "Net VSS: has ... opens at (x1, y1) (x2, y2)" lines.
proc rpt_opens {rpt} {
  set res {}
  if {[catch {open $rpt r} f]} { return $res }
  foreach l [split [read $f] "\n"] {
    if {[regexp {^Net (\S+):.*opens at \(([-\d.]+), ([-\d.]+)\) \(([-\d.]+), ([-\d.]+)\)} $l -> n x1 y1 x2 y2]} {
      lappend res [list "Net $n" [list $x1 $y1 $x2 $y2]]
    }
  }
  close $f
  return $res
}

proc run_conn {tag} {
  set sp {}
  clearDrc
  if {![catch {verifyConnectivity -type special -noAntenna -error 100000 -report conn_${tag}_special.rpt}]} {
    set sp [conn_opens]
    if {![llength $sp]} { set sp [rpt_opens conn_${tag}_special.rpt] }
  }
  clearDrc
  verifyConnectivity -noAntenna -error 100000 -report conn_${tag}.rpt
  set all [conn_opens]
  if {![llength $all]} { set all [rpt_opens conn_${tag}.rpt] }
  return [list $all $sp]
}

proc count_by_net {opens} {
  array set c {}
  foreach o $opens { set n [lindex $o 0]; if {![info exists c($n)]} { set c($n) 0 }; incr c($n) }
  set s {}
  foreach n [lsort [array names c]] { lappend s "$n:$c($n)" }
  return [join $s " "]
}

set ckpt $::env(PG_DIAG_CKPT)
set top  [expr {[info exists ::env(PG_DIAG_TOP)] ? $::env(PG_DIAG_TOP) : "Tile_MemCore"}]
set errs [open errors.txt w]

if {[catch {restoreDesign $ckpt $top} e]} {
  out $errs "restoreDesign failed: $e"
  close $errs
  exit 1
}
setMultiCpuUsage -localCpu 8

#-------------------------------------------------------------------------
# summary.txt
#-------------------------------------------------------------------------
set fh [open summary.txt w]
if {[catch {
  out $fh "checkpoint: $ckpt"
  out $fh "die box:  [dbGet top.fPlan.box]"
  out $fh "core box: [dbGet top.fPlan.coreBox]"
  set rows [dbGet -e top.fPlan.rows]
  set ys {}
  foreach r $rows { lappend ys [dbGet $r.box_lly] }
  set ys [lsort -real -unique $ys]
  out $fh "rows: [llength $rows] row objects, [llength $ys] distinct y, first y [lindex $ys 0], last y [lindex $ys end], row height [dbGet [lindex $rows 0].box_sizey]"
  out $fh "routing layers by Z:"
  for {set z 1} {$z <= 16} {incr z} {
    if {[catch {dbGetLayerByZ $z} l] || $l eq "" || $l eq "0x0"} { break }
    out $fh "  Z$z [dbGet $l.name] dir=[dbGet $l.direction] minWidth=[dbGet $l.minWidth] pitchX=[dbGet $l.pitchX] pitchY=[dbGet $l.pitchY]"
  }
  out $fh "block (macro) instances:"
  foreach i [dbGet -e -p2 top.insts.cell.baseClass block] {
    out $fh "  [dbGet $i.name] [dbGet $i.cell.name] box=[dbGet $i.box] orient=[dbGet $i.orient]"
  }
  out $fh "route blockages:"
  foreach b [dbGet -e top.fPlan.rBlkgs] {
    out $fh "  name=[dbGet $b.name] layer=[lname [dbGet $b.layer]] pgNetOnly=[dbGet $b.isPGNetOnly] exceptPGNet=[dbGet $b.isExceptPGNet] boxes=[dbGet $b.boxes]"
  }
  out $fh "PG nets, special wires by layer/shape, special vias, regular wires:"
  foreach n [dbGet -e top.nets.name] {
    set net [dbGet -p top.nets.name $n]
    if {![dbGet $net.isPwrOrGnd]} { continue }
    array unset sw
    foreach w [dbGet -e $net.sWires] {
      set k "[lname [dbGet $w.layer]]/[dbGet $w.shape]"
      if {![info exists sw($k)]} { set sw($k) 0 }
      incr sw($k)
    }
    out $fh "  $n: sWires [llength [dbGet -e $net.sWires]] sVias [llength [dbGet -e $net.sVias]] wires [llength [dbGet -e $net.wires]]"
    foreach k [lsort [array names sw]] { out $fh "      $k $sw($k)" }
  }
} e]} { out $errs "summary: $e" }
close $fh

#-------------------------------------------------------------------------
# opens.txt: every open and what lies in its box
#-------------------------------------------------------------------------
set m1 [dbGet [dbGetLayerByZ 1].name]
# the M3 stripes' layer (power-strategy-dualmesh.tcl: stacked vias M1..Z3);
# PG_DIAG_TOPZ overrides it for testing on other stacks
set topz [expr {[info exists ::env(PG_DIAG_TOPZ)] ? $::env(PG_DIAG_TOPZ) : 3}]
set m3 [dbGet [dbGetLayerByZ $topz].name]
set die_area [box_area [dbGet top.fPlan.box]]

lassign [run_conn before] opens sp_opens
set fh [open opens.txt w]
if {[catch {
  out $fh "opens (all): [llength $opens] ([count_by_net $opens]); special-wire-only check: [llength $sp_opens] ([count_by_net $sp_opens])"
  set idx 0
  foreach o $opens {
    lassign $o msg box
    incr idx
    out $fh ""
    out $fh "OPEN $idx: $msg box=$box"
    if {[box_area $box] > 0.25 * $die_area} {
      out $fh "  (spans >25% of the die: the net's main piece, see conn_before.rpt; objects not listed)"
      continue
    }
    set ws [q $box sWire]
    foreach w $ws {
      out $fh "  sWire net=[dbGet $w.net.name] layer=[lname [dbGet $w.layer]] shape=[dbGet $w.shape] status=[dbGet $w.status] box=[dbGet $w.box]"
    }
    foreach w [q $box wire] {
      out $fh "  wire  net=[dbGet $w.net.name] layer=[lname [dbGet $w.layer]] box=[dbGet $w.box]"
    }
    set vias [q $box sViaInst]
    out $fh "  sViaInsts in box: [llength $vias]"
    foreach v [lrange $vias 0 9] {
      out $fh "    via net=[attr $v net.name] cell=[attr $v via.name] at=[attr $v pt]"
    }
    set insts [q $box inst "" 1]
    array unset ic
    set logic 0
    foreach i $insts {
      set c [dbGet $i.cell.name]
      if {![info exists ic($c)]} { set ic($c) 0 }
      incr ic($c)
      if {![attr $i isPhysOnly 0] && [attr $i cell.baseClass] eq "core"} { incr logic }
    }
    out $fh "  instances overlapping: [llength $insts] (non-physical-only core cells: $logic)"
    foreach c [lsort [array names ic]] { out $fh "    $c x$ic($c)" }
    foreach i [lrange $insts 0 4] {
      out $fh "    e.g. [dbGet $i.name] [dbGet $i.cell.name] box=[dbGet $i.box] orient=[dbGet $i.orient] physOnly=[attr $i isPhysOnly ?]"
    }
    # what an M3 stripe would have to via down through: M3 special wires
    # crossing the box, and blockages within 1 um
    set m3w [q $box sWire $m3]
    out $fh "  $m3 special wires crossing: [llength $m3w]"
    foreach w [lrange $m3w 0 5] {
      out $fh "    net=[dbGet $w.net.name] shape=[dbGet $w.shape] box=[dbGet $w.box]"
    }
    foreach b [q [grow $box 1.0] rBlkg] {
      out $fh "  rBlkg near: name=[dbGet $b.name] layer=[lname [dbGet $b.layer]] pgNetOnly=[attr $b isPGNetOnly ?] exceptPGNet=[attr $b isExceptPGNet ?] boxes=[attr $b boxes]"
    }
    foreach i [q [grow $box 2.0] inst] {
      if {[dbGet $i.cell.baseClass] eq "block"} {
        out $fh "  macro within 2 um: [dbGet $i.name] box=[dbGet $i.box]"
      }
    }
  }
} e]} { out $errs "opens: $e" }
close $fh

#-------------------------------------------------------------------------
# drc.rpt + drc_summary.txt
#-------------------------------------------------------------------------
proc drc_classes {} {
  array set c {}
  set n 0
  foreach m [dbGet -e top.markers] {
    if {[dbGet $m.type] eq "Connectivity"} { continue }
    incr n
    set msg [dbGet $m.message]
    set kind [expr {[string match "*Routing Blockage*" $msg] ? "vs-RoutingBlockage" : ([string match "*Blockage*" $msg] ? "vs-OtherBlockage" : "real-geometry")}]
    set k "$kind | [dbGet $m.subType] | [lname [dbGet $m.layer]]"
    if {![info exists c($k)]} { set c($k) 0 }
    incr c($k)
  }
  set s [list "total $n"]
  foreach k [lsort [array names c]] { lappend s "  $c($k)  $k" }
  return [join $s "\n"]
}

if {[catch {
  clearDrc
  set_verify_drc_mode -limit 100000
  verify_drc -report drc.rpt
  set fh [open drc_summary.txt w]
  out $fh "verify_drc -limit 100000 (signoff ran with the default 1000)"
  out $fh [drc_classes]
  close $fh
} e]} { out $errs "drc: $e" }

#-------------------------------------------------------------------------
# trials.txt: in-memory via fixes (never saved)
#-------------------------------------------------------------------------
set fh [open trials.txt w]
if {[catch {
  set small {}
  foreach o $opens {
    set b [lindex $o 1]
    if {[box_area $b] <= 0.25 * $die_area} { lappend small [grow $b 0.5] }
  }
  out $fh "baseline: opens [llength $opens] ([count_by_net $opens])"
  if {[llength $small]} {
    set nets [lsort -unique [lmap o $opens {lindex [lindex $o 0] end}]]
    # T1: what the flow's own via generator does when asked again (DRC-clean vias only)
    setViaGenMode -reset
    setViaGenMode -ignore_DRC false
    set v0 [llength [dbGet -e top.nets.sVias]]
    editPowerVia -add_vias 1 -nets $nets -bottom_layer $m1 -top_layer $m3 -area $small
    set v1 [llength [dbGet -e top.nets.sVias]]
    lassign [run_conn t1] o1 s1
    out $fh "T1 editPowerVia $m1..$m3 in the open boxes, ignore_DRC false: +[expr {$v1-$v0}] vias, opens [llength $o1] ([count_by_net $o1])"
    # T2: force the vias, then see which DRCs that creates in those boxes
    setViaGenMode -ignore_DRC true
    editPowerVia -add_vias 1 -nets $nets -bottom_layer $m1 -top_layer $m3 -area $small
    set v2 [llength [dbGet -e top.nets.sVias]]
    lassign [run_conn t2] o2 s2
    out $fh "T2 same with ignore_DRC true: +[expr {$v2-$v1}] more vias, opens [llength $o2] ([count_by_net $o2])"
    clearDrc
    set_verify_drc_mode -limit 100000
    verify_drc -report drc_after_t2.rpt
    out $fh "  verify_drc after T2 (compare drc_summary.txt, before any trial):"
    out $fh "  [string map {"\n" "\n  "} [drc_classes]]"
    set_verify_drc_mode -reset
  }
} e]} { out $errs "trials: $e" }
close $fh

close $errs
exit
