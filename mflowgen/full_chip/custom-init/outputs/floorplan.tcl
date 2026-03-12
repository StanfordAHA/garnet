#=========================================================================
# floorplan.tcl
#=========================================================================
set fp_width          3924.72
set fp_height         4084.92

set vert_pitch [dbGet top.fPlan.coreSite.size_y]
set hori_pitch [dbGet top.fPlan.coreSite.size_x]


set die_ring_hori     16.2
set die_ring_vert     17.64
set prs_width         58.32
set prs_height        57.96
set fp_margin_width   [expr $die_ring_hori + $prs_width + 8 * $hori_pitch]
set fp_margin_height  [expr $die_ring_vert + $prs_height + 2 * $vert_pitch]

floorPlan \
    -coreMarginsBy die \
    -d ${fp_width} ${fp_height} ${fp_margin_width} ${fp_margin_height} ${fp_margin_width} ${fp_margin_height}

