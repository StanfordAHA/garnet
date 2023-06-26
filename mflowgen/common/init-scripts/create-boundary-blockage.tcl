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

# get the white space width
set ws_left   [expr $pitch_x * $ADK_WHITE_SPACE_FACTOR_HORI]
set ws_right  [expr $pitch_x * $ADK_WHITE_SPACE_FACTOR_HORI]
set ws_top    [expr $pitch_y * $ADK_WHITE_SPACE_FACTOR_VERT]
set ws_bottom [expr $pitch_y * $ADK_WHITE_SPACE_FACTOR_VERT]

# Compute the bbox for the placement blockage on 4 sides
#                llx                        lly                       urx       ury
set pblk_bottom "0                          0                         $fp_width $ws_bottom"
set pblk_top    "0                          [expr $fp_height-$ws_top] $fp_width $fp_height"
set pblk_left   "0                          0                         $ws_left  $fp_height"
set pblk_right  "[expr $fp_width-$ws_right] 0                         $fp_width $fp_height"

# Put the placement blockage to form white space
createPlaceBlockage \
    -boxList [list $pblk_bottom $pblk_top $pblk_left $pblk_right] \
    -name boundary_ws \
    -type hard

# create route blockage
set blkg_layer "m1 m2 m3 m4 m5 m6 m7 m8"
set ws_left   $ADK_BOUNDARY_ROUTE_BLOCKAGE_WIDTH
set ws_right  $ADK_BOUNDARY_ROUTE_BLOCKAGE_WIDTH
set ws_top    $ADK_BOUNDARY_ROUTE_BLOCKAGE_WIDTH
set ws_bottom $ADK_BOUNDARY_ROUTE_BLOCKAGE_WIDTH

# Compute the bbox of routing blockage on 4 sides
#                   dimension-x                dimension-y 
set rblk_bottom_ll "0                          0"
set rblk_bottom_ur "$fp_width                  $ws_bottom"

#                   dimension-x                dimension-y 
set rblk_top_ll    "0                          [expr $fp_height-$ws_top]"
set rblk_top_ur    "$fp_width                  $fp_height"

#                   dimension-x                dimension-y 
set rblk_left_ll   "0                          0"
set rblk_left_ur   "$ws_left                   $fp_height"

#                   dimension-x                dimension-y 
set rblk_right_ll  "[expr $fp_width-$ws_right] 0"
set rblk_right_ur  "$fp_width                  $fp_height"

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
