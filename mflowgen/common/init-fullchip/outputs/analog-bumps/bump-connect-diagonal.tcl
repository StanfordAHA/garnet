# Build a diagonal (45-degree) wire from bump a to bump b
# Example: bump_connect_diagonal Bump_629.25.5 Bump_654.26.4

set TEST 0
proc bump_connect_diagonal { b1 b2 net } {
    set polygon [build_polygon $b1 $b2]
    set cmd [draw_polygon_cmd $polygon CVSS]
    print $cmd
    {*}$cmd
}
proc test_bump_connect_diagonal {} {
    set b1 Bump_629.25.5
    set b2 Bump_654.26.4

    deselectAll
    select_obj bump:pad_frame/$b1
    select_obj bump:pad_frame/$b2
    sleep 1; # Give it time do display the two bumps

    bump_connect_diagonal $b1 $b2 CVSS
}
if { $TEST } { test_bump_connect_diagonal }


proc build_point {x y} {
    return [ format "{%.3f %.3f}" $x $y ]
}
if { $TEST } { build_point 0 4900 }

proc build_points_and_caps { x y start } {
    #
    #           t1        t2
    #            /---------\
    #           /           \
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
if {$TEST} {
    set x 1277.925; set y 4573.855
    print [ build_points_and_caps $x $y ll ];\
    print "{1328.659,4603.375} {1316.231,4603.375} {1307.445,4612.161} {1307.445,4624.589}"
}

proc build_polygon {b1 b2} {
    # Build the polygon that diagonally connects bumps cb1, cb2

    set cb1x [get_db bump:pad_frame/$b1 .location.x]
    set cb1y [get_db bump:pad_frame/$b1 .location.y]

    set cb2x [get_db bump:pad_frame/$b2 .location.x]
    set cb2y [get_db bump:pad_frame/$b2 .location.y]

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

proc draw_polygon_cmd { polygon net } {
    # Build but do not execute the command for drawing the polygon
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
