# In this script: 
#   bump_connect_diagonal: connect two or more bumps along a diagonal line
#   bump_connect_orthogonal: connect two or more bumps along an orthogonal line
#   bump2wire_up: connect one or more bumps in a line to a wire above them

set TEST 0
if {0} {
    # Cut'n'paste to test script(s)
    source inputs/analog-bumps/bump-connect-diagonal.tcl
    bump_connect_diagonal CVDD *26.3 *25.4 *24.5 *23.6 *22.7
    bump_connect_diagonal CVSS *25.5 *26.4
}
# Build an orthogonal (horizontal or vertical) wire connecting two or more bumps
# Example: bump_connect_diagonal Bump_629.25.5 Bump_654.26.4
proc bump_connect_orthogonal { net args } {
    # bump_connect_orthogonal <netname> <bumplist>
    # Examples:
    #     bump_connect_orthogonal CVSS Bump_629.25.5 Bump_654.26.4
    #     bump_connect_orthogonal CVSS *25.5 *26.4
    set bumps []
    foreach b $args {
        dbGet top.bumps.name $b
        set last_bump [dbGet top.bumps.name $b]
        assignPGBumps -nets $net -bumps $last_bump
        lappend bumps $last_bump
    }
    set first_bump [lindex $bumps 0]
    echo first=$first_bump; echo last=$last_bump; echo bumps=\"$bumps\"

    echo build_rectangle $first_bump $last_bump
    set rectangle [build_rectangle $first_bump $last_bump]
    add_shape -net $net -status FIXED -rect $rectangle -layer AP -shape IOWIRE   
}
if {0} {
    # cut'n'paste to test
    bump_connect_orthogonal CVDD *23.5 *23.6
    bump_connect_orthogonal CVDD *22.6 *22.7 *22.8 *22.9

    bump_connect_orthogonal CVSS *25.5 *25.6 *25.7 *25.8
    bump_connect_orthogonal CVSS *25.8 *24.8 *23.8
    bump_connect_orthogonal CVSS *23.8 *23.7
    bump_connect_orthogonal CVSS *25.7 

    bump2wire_up  CVSS Bump_631.25.7
}
proc bump2wire_up { net args} {
    # Begin at first bump b1 in list <args>;
    # search upward until find a shape (wire) connected to CVSS on the AP (M10) layer;
    # connect the two, along with all bumps on the list, using net <net>;
    # is this crazy enough.
    #
    # Usage:   bump2wire_up <net> <bumplist>
    # Example: bump2wire_up CVSS Bump_631.25.7 Bump_657.26.7

    # Make sure all bumps in list are assigned to <net>
    foreach b $args {
        assignPGBumps -nets $net -bumps [dbGet top.bumps.name $b]
    }
    set b1 [lindex $args 0]; # First bump in list is source for wire
    # set b1 Bump_631.25.7

    set LLX [dbGet [dbGet -p top.bumps.name $b1].bump_shape_center_x]
    set LLY [dbGet [dbGet -p top.bumps.name $b1].bump_shape_center_y]

    set wire_width 30
    set LLX [expr $LLX - ($wire_width / 2) ]
    set LLY [expr $LLY - ($wire_width / 2) ]
    build_wire_up $net $LLX $LLY $wire_width
}
if {0} { # cut-n-paste to test
    bump2wire_up CVSS Bump_631.25.7 Bump_657.26.7
}

proc build_wire_up { net LLX LLY wire_width } {
    # Given LL corner of a wire of width <wire_width>,
    # run wire upward until it connects to the next
    # rectangular RDL wire it finds. All wires should be part of <net>
    # Error if cannot find a connecting wire within 600u of starting point.

    # Step upward from LLY in increments of 10u;
    # stop when we hit a rectangular RDL wire and/or if we go more than 600u
    set DBG 0
    set step [expr $wire_width / 2]; set max 600
    set start_y [expr $LLY + $step + $wire_width]; set end_y [expr $LLY + $max ];
    for { set y $start_y } { $y < $end_y } { set y [expr $y + 15] } {
        if {$DBG} { echo "  searching x=$LLX y=$y..." }
        # set w [find_horizontal_CVSS_wire $net $LLX $y ]
        set w [get_wire $net $LLX $y ]
        if { $w != 0} { break }
    }
    if { $w == 0 } { echo "@file_info ERROR could not find connecting wire" }
    # select_obj $w
    set URY [dbGet $w.box_ury]
    set URX [expr $LLX + $wire_width]
    set rectangle "$LLX $LLY   $URX $URY"
    add_shape -net $net -status FIXED -rect $rectangle -layer AP -shape IOWIRE   
    # return "$LLX $LLY   $URX $URY"
}
if {0} { # cut-n-paste to test
    build_wire_up CVSS 1307.445 4429.905 30.0
}

proc get_wire { net px py } {
    # If (px,py) is in a rectangular wire segment of <net>
    # then return a pointer to the wire; else return FALSE (0)

    # Get list of rectangular wires, i.e. defined by exactly four polyPt corners
    set criteria { [llength [lindex .polyPts 0] ] == 4 }
    set wires [dbGet [dbGet -p top.nets.name $net].sWires $criteria]

    foreach w $wires {
        set llx [dbGet $w.box_llx]; set lly [dbGet $w.box_lly]; 
        set urx [dbGet $w.box_urx]; set ury [dbGet $w.box_ury]; 
        if {($llx < $px) && ($urx > $px) && ($lly<$py) && ($ury>$py)} {
            return $w; # Found a wire
        }
    }
    return 0; # Did not find a wire.
}
if {0} { # cut-n-paste to test
    select_obj [get_wire CVSS 1318 4700]
    select_obj [get_wire CVDD 1318 4740]
    select_obj [get_wire CVSS 1318 4444]
    select_obj [get_wire CVSS 1307 4442]
}

# Build a diagonal (45-degree) wire connecting two or more bumps
# Example: bump_connect_diagonal Bump_629.25.5 Bump_654.26.4
proc bump_connect_diagonal { net args } {
    # bump_connect_diagonal <netname> <bumplist>
    # Examples:
    #     bump_connect_diagonal CVSS Bump_629.25.5 Bump_654.26.4
    #     bump_connect_diagonal CVSS *25.5 *26.4
    set bumps []
    foreach b $args {
        dbGet top.bumps.name $b
        set last_bump [dbGet top.bumps.name $b]
        assignPGBumps -nets $net -bumps $last_bump
        lappend bumps $last_bump
    }
    set first_bump [lindex $bumps 0]
    echo first=$first_bump; echo last=$last_bump; echo bumps=\"$bumps\"

    echo build_polygon $first_bump $last_bump
    set polygon [build_polygon $first_bump $last_bump]
    set cmd [draw_polygon_cmd $polygon $net]
    print $cmd
    {*}$cmd
}
if {0} {
    # Cut'n'paste to test
    bump_connect_diagonal CVDD *26.3 *25.4 *24.5 *23.6 *22.7
    redraw; sleep 1
    bump_connect_diagonal CVSS *25.5 *26.4
    redraw; sleep 1
}


proc build_points_and_caps { x y start } {
    #
    #           t1        t2
    #            /---------\
    #           /           \
    #       l1 /             \ r1
    #          |             |    
    #          |             |    
    #          |             |    
    #       l2 \             / r2
    #           \           /
    #            \_________/
    # 
    #            b1        b2
    #             
    # Build wire endcaps for bump with LL at x,y

    # x,y distances in above diagram
    set SS [expr 38.306 - 29.520]; # shortseg
    set LS [expr 50.734 - 38.306]; # longseg
    set S2 [expr $SS + $LS]
    set S3 [expr $SS + $LS + $SS]

    # x,y coordinates of each bump in the above diagram
    foreach p { l1x l2x b1y b2y } { set points($p)   0 }
    foreach p { t1x b1x l2y r2y } { set points($p) $SS }
    foreach p { t2x b2x l1y r1y } { set points($p) $S2 }
    foreach p { r1x r2x t1y t2y } { set points($p) $S3 }

    # Offset from LL bump to LL wire in center of bump
    #   set off_x [expr 1307.445 - 1277.925] ; # 29.52
    #   set off_y [expr 4603.375 - 4573.855] ; # 29.52

    foreach p { l1x l2x r1x r2x t1x t2x b1x b2x } {
        set points($p) [ expr $points($p) + $x + 29.52 ]
    }
    foreach p { l1y l2y r1y r2y t1y t2y b1y b2y } {
        set points($p) [ expr $points($p) + $y + 29.52 ]
    }

    proc build_point {x y} { format "{%.3f %.3f}" $x $y }
    set b1 [ build_point $points(b1x) $points(b1y) ]
    set l1 [ build_point $points(l1x) $points(l1y) ]
    set t1 [ build_point $points(t1x) $points(t1y) ]
    set r1 [ build_point $points(r1x) $points(r1y) ]
    
    set b2 [ build_point $points(b2x) $points(b2y) ]
    set l2 [ build_point $points(l2x) $points(l2y) ]
    set t2 [ build_point $points(t2x) $points(t2y) ]
    set r2 [ build_point $points(r2x) $points(r2y) ]

    # Wire can start at UL, UR, LR, or LL end
    # Points go clockwise to match what I saw in innovus polygon
    switch $start {
        ul { set cap "$l2 $l1 $t1 $t2" }
        ur { set cap "$t1 $t2 $r1 $r2" }
        lr { set cap "$r1 $r2 $b2 $b1" }
        ll { set cap "$b2 $b1 $l2 $l1" }
    }
    return $cap
}
set TEST 0; if {$TEST} {
    set x 1277.925; set y 4573.855
    print [ build_points_and_caps $x $y ll ];\
    print "{1328.659,4603.375} {1316.231,4603.375} {1307.445,4612.161} {1307.445,4624.589}"
}

proc build_rectangle {b1 b2} {
    # Build the rectangle (wire) that connects bumps cb1, cb2 horizonally or vertically

    # NO! design name will not always be "pad_frame"
    # set cb1x [get_db bump:pad_frame/$b1 .location.x]

    # LL corner of each bump, I think
    set cb1x [get_db [get_db bumps $b1] .location.x]
    set cb1y [get_db [get_db bumps $b1] .location.y]

    set cb2x [get_db [get_db bumps $b2] .location.x]
    set cb2y [get_db [get_db bumps $b2] .location.y]
    


    if       {$cb1x < $cb2x} { set rectangle [connect_left_right $b1 $b2]
    } elseif {$cb1x > $cb2x} { set rectangle [connect_left_right $b2 $b1]
    } elseif {$cb1y < $cb2y} { set rectangle [connect_top_bottom $b2 $b1]
    } elseif {$cb1y > $cb2y} { set rectangle [connect_top_bottom $b1 $b2]
    } else   { puts "ERROR they are the same bump" }
}
# build_rectangle Bump_577.23.5 Bump_603.24.5

proc connect_top_bottom { b1 b2 } {
    # Rectangle is a 30u wire
    set wire_width 30

    # Connect b1 (top) to b2 (bottom)
    set LLX [dbGet [dbGet -p top.bumps.name $b2].bump_shape_center_x]
    set LLY [dbGet [dbGet -p top.bumps.name $b2].bump_shape_center_y]
    set LLX [expr $LLX - ($wire_width / 2) ]
    set LLY [expr $LLY - ($wire_width / 2) ]
    
    set URX [dbGet [dbGet -p top.bumps.name $b1].bump_shape_center_x]
    set URY [dbGet [dbGet -p top.bumps.name $b1].bump_shape_center_y]
    set URX [expr $URX + ($wire_width / 2) ]
    set URY [expr $URY + ($wire_width / 2) ]
    return "$LLX $LLY   $URX $URY"
}
proc connect_left_right { b1 b2 } {
    # Rectangle is a 30u wire
    set wire_width 30

    # Connect b1->b2 horizontally
    set LLX [dbGet [dbGet -p top.bumps.name $b1].bump_shape_center_x]
    set LLY [dbGet [dbGet -p top.bumps.name $b1].bump_shape_center_y]
    set LLX [expr $LLX - ($wire_width / 2) ]
    set LLY [expr $LLY - ($wire_width / 2) ]
    
    set URX [dbGet [dbGet -p top.bumps.name $b2].bump_shape_center_x]
    set URY [dbGet [dbGet -p top.bumps.name $b2].bump_shape_center_y]
    set URX [expr $URX + ($wire_width / 2) ]
    set URY [expr $URY + ($wire_width / 2) ]
    return "$LLX $LLY   $URX $URY"
}
if {0} {
    # Cut'n'paste to test proc
    echo [build_rectangle Bump_577.23.5 Bump_578.23.6]; \
    echo [build_rectangle Bump_578.23.6 Bump_577.23.5]

    echo [build_rectangle Bump_577.23.5 Bump_603.24.5]; \
    echo [build_rectangle Bump_603.24.5 Bump_577.23.5]
}
    
proc build_polygon {b1 b2} {
    # Build the polygon that diagonally connects bumps cb1, cb2

    set cb1x [get_db [get_db bumps $b1] .location.x]
    set cb1y [get_db [get_db bumps $b1] .location.y]

    set cb2x [get_db [get_db bumps $b2] .location.x]
    set cb2y [get_db [get_db bumps $b2] .location.y]

    # Sort bumps into higher and lower bump
    if { $cb1y < $cb2y } { 
        set cblox $cb1x; set cbloy $cb1y; 
        set cbhix $cb2x; set cbhiy $cb2y;
    } else { 
        set cblox $cb2x; set cbloy $cb2y;
        set cbhix $cb1x; set cbhiy $cb1y;
    }
    # Connect them
    if { $cblox < $cbhix } {
        # Wire travels from ll to ur
        # set bottom_end  $bottomcap_ll
        # set top_end     $ur_cap
        set bottom_end  [ build_points_and_caps $cblox $cbloy ll ]
        set top_end     [ build_points_and_caps $cbhix $cbhiy ur ]

    } else {
        # Wire travels from lr to ul
        # set bottom_end  $bottomcap_lr
        # set top_end     $ul_cap
        set bottom_end  [ build_points_and_caps $cblox $cbloy lr ]
        set top_end     [ build_points_and_caps $cbhix $cbhiy ul ]
    }
    set polygon "$bottom_end $top_end"
    return $polygon
}
proc test_build_polygon {} {

    set b1 Bump_658.26.8; set bump1_x 1451.395; set bump1_y 4573.855
    set b2 Bump_631.25.7; set bump2_x 1277.925; set bump2_y 4400.385
    
    # set p2 [ build_polygon $bump2_x $bump2_y $bump1_x $bump1_y ]
    # set p1 [ build_polygon $bump1_x $bump1_y $bump2_x $bump2_y ]

    set p2 [ build_polygon $b1 $b2]
    set p1 [ build_polygon $b1 $b2]

    print "p1: $p1"; print "p2: $p2"
    if { $p1 == $p2 } { echo "p1 == p2" } else { echo ERROR }
    set answer {{1328.659 4429.905} {1316.231 4429.905} {1307.445 4438.691} {1307.445 4451.119} {1489.701 4633.375} {1502.129 4633.375} {1510.915 4624.589} {1510.915 4612.161}}
    if { $p1 == $answer } { echo "p1 == p2 == right answer" } else { echo ERROR }
    return $p1
}
if {$TEST} { test_build_polygon }

# Build but do not execute the command for drawing the polygon
proc draw_polygon_cmd { polygon net } {
    # Example:
    #  set cmd [draw_polygon_cmd $polygon CVSS]
    #  print $cmd; {*}$cmd
    concat \
        "add_shape"            \
        " -net $net"           \
        " -status FIXED"       \
        " -polygon {$polygon}" \
        " -layer AP"           \
        " -shape IOWIRE"
}
if {$TEST} {
    set p1 [ test_build_polygon ]
    set cmd [ draw_polygon_cmd_string $p1 CVSS ]
    print $cmd
    {*}$cmd
}

# NOTES: How I found the offsets
# 1. Find existing diagonal polygon and copy down the coordinates
# 2. Seperate coordinates into exes and wise and find offsets
# 
# exes = "1068.454 1077.24 1077.24 81.719 969.291 960.505 960.505 1056.026"
# print exes;
# n = split(exes, ea, " "); # First element is '1' not '0'
# for (i=1; i<=n; i++) { print ea[i] - bx }
# 
# wise = "4546.64 4537.854 4525.426 4429.905 4429.905 4438.691 4451.119 4546.64"
# ny = split(wise, ay, " "); # First element is '1' not '0'
# for (i=1; i<=ny; i++) { print ay[i] - by }
# 
# for (i=1; i<=ny; i++) {
#   printf("    %7.3f,%7.3f\n", ea[i] - bx, ay[i] - by) }
# 
#           t1        t2
#            /---------\.
#           /           \.
#       l1 /             \ r1
#          |             |    
#          |             |    
#          |             |    
#          |             |    
#       l2 \             / r2
#           \           /
#            \_________/
# 
#            b1        b2
