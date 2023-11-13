#=========================================================================
# create-boundary-blockage.tcl
#=========================================================================
# This script is used to put placement/routing blockage at the design
# boundaries to create white spaces.
# Author : 
# Date   : 

# floorplan parameters
set pitch_x [dbGet top.fPlan.coreSite.size_x]
set pitch_y [dbGet top.fPlan.coreSite.size_y]
set fp_width  [dbGet top.fPlan.box_urx]
set fp_height [dbGet top.fPlan.box_ury]

set core_box_llx [dbGet top.fPlan.coreBox_llx]
set core_box_lly [dbGet top.fPlan.coreBox_lly]
set core_box_urx [dbGet top.fPlan.coreBox_urx]
set core_box_ury [dbGet top.fPlan.coreBox_ury]

set box_llx 0
set box_lly 0
set box_urx $fp_width
set box_ury $fp_height

# get the white space width
set ws_left   [expr $pitch_x * $ADK_WHITE_SPACE_FACTOR_HORI]
set ws_right  [expr $pitch_x * $ADK_WHITE_SPACE_FACTOR_HORI]
set ws_top    [expr $pitch_y * $ADK_WHITE_SPACE_FACTOR_VERT]
set ws_bottom [expr $pitch_y * $ADK_WHITE_SPACE_FACTOR_VERT]

# Compute the bbox for the placement blockage on 4 sides
#                llx                       lly                     urx                        ury
set pblk_bottom "$box_llx                  $box_lly                $box_urx                   [expr $box_lly + $ws_bottom]"
set pblk_top    "$box_llx                  [expr $box_ury-$ws_top] $box_urx                   $box_ury"
set pblk_left   "$box_llx                  $box_lly                [expr $box_llx + $ws_left] $box_ury"
set pblk_right  "[expr $box_urx-$ws_right] $box_lly                $box_urx                   $box_ury"

# Put the placement blockage to form white space
# createPlaceBlockage \
#     -boxList [list $pblk_bottom $pblk_top $pblk_left $pblk_right] \
#     -name boundary_ws \
#     -type hard

# create route blockage
set blkg_layer "m1 m2 m3 m4 m5 m6 m7 m8"
set ws_left   $ADK_BOUNDARY_ROUTE_BLOCKAGE_WIDTH
set ws_right  $ADK_BOUNDARY_ROUTE_BLOCKAGE_WIDTH
set ws_top    $ADK_BOUNDARY_ROUTE_BLOCKAGE_WIDTH
set ws_bottom $ADK_BOUNDARY_ROUTE_BLOCKAGE_WIDTH

#                   dimension-x                dimension-y 
set rblk_bottom_ll "$box_llx                   $box_lly"
set rblk_bottom_ur "$box_urx                   [expr $box_lly + $ws_bottom]" 
#                   dimension-x                dimension-y 
set rblk_top_ll    "$box_llx                   [expr $box_ury-$ws_top]"
set rblk_top_ur    "$box_urx                   $box_ury"
#                   dimension-x                dimension-y 
set rblk_left_ll   "$box_llx                   $box_lly"
set rblk_left_ur   "[expr $box_llx + $ws_left] $box_ury"
#                   dimension-x                dimension-y 
set rblk_right_ll  "[expr $box_urx-$ws_right]  $box_lly"
set rblk_right_ur  "$box_urx                   $box_ury"

# createRouteBlk command requires the bbox to be specified in position list
set rblk_list [list \
        $rblk_bottom_ll \
        $rblk_bottom_ur \
        $rblk_top_ll \
        $rblk_top_ur \
        $rblk_left_ll \
        $rblk_left_ur \
        $rblk_right_ll \
        $rblk_right_ur \
    ]

# Create the routing blockage
createRouteBlk \
    -layer $blkg_layer \
    -boxList $rblk_list \
    -exceptpgnet \
    -name Route_blkg_boundry
