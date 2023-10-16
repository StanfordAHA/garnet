#=========================================================================
# floorplan.tcl
#=========================================================================
# Author :
# Date   :

#-------------------------------------------------------------------------
# Floorplan variables
#-------------------------------------------------------------------------

set core_aspect_ratio   1.00; # Aspect ratio 1.0 for a square chip
set core_density_target $::env(core_density_target);

# Compute netlist cell area
set cell_area 0
foreach c [dbGet head.libCells {.numRefs > 0}] {
    set insts [dbGet $c.numRefs]
    set area [expr $insts * [dbGet $c.size_x] * [dbGet $c.size_y]]
	set cell_area [expr $cell_area + $area]
}

# Reserve white space at the boundary
set pitch_x [dbGet top.fPlan.coreSite.size_x]
set pitch_y [dbGet top.fPlan.coreSite.size_y]
set ws_left   [expr $pitch_x * $ADK_WHITE_SPACE_FACTOR_HORI]
set ws_right  [expr $pitch_x * $ADK_WHITE_SPACE_FACTOR_HORI]
set ws_top    [expr $pitch_y * $ADK_WHITE_SPACE_FACTOR_VERT]
set ws_bottom [expr $pitch_y * $ADK_WHITE_SPACE_FACTOR_VERT]

# Compute chip size
# (1) core_aspect_ratio = width / height
# (2) cell_area         = width * height * core_density_target
set height [expr sqrt($cell_area / $core_density_target / $core_aspect_ratio)]
set width  [expr $core_aspect_ratio * $height]

# Round-up to the nearest round_y/x and include white space
set round_y [expr 2 * $pitch_y]
set round_x [expr 4 * $pitch_x]
set height [expr int(ceil($height / $round_y)) * $round_y + $ws_top + $ws_bottom]
set width  [expr int(ceil($width  / $round_x)) * $round_x + $ws_left + $ws_right]

#-------------------------------------------------------------------------
# Floorplan
#-------------------------------------------------------------------------
floorPlan -d $width $height 0 0 0 0
setFlipping s
planDesign
