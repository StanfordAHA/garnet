

#=========================================================================
# Create always-on domain region 
#=========================================================================

# Dont dont_touch constraints
source inputs/dont-touch-constraints.tcl

set polypitch_y [dbGet top.fPlan.coreSite.size_y]
set polypitch_x [dbGet top.fPlan.coreSite.size_x]

# AON height should be even value so that the AON domain
#  start an even row else it can block the spacing between 
# power switches that are placed in staggered manner
# causing latch up DRCs

# Convert width and height param from # of pitches to
# actual coordinates
set aon_height [expr $aon_height * $polypitch_y]
set aon_width [expr $aon_width * $polypitch_x]

# Calculate bbox of AON domain
set aon_llx [expr $width/2 - $aon_width/2 + $aon_horiz_offset]
set aon_lly [expr $height/2 - $aon_height/2 + $aon_vert_offset]
# Ensure that LLX and LLY are on grid
set aon_llx_snap [expr ceil($aon_llx/$polypitch_x)*$polypitch_x]
set aon_lly_snap [expr ceil($aon_lly/$polypitch_y)*$polypitch_y]
# Calculate URX and URY using width/height (guaranteed to be on grid)
set aon_urx [expr $aon_llx_snap + $aon_width]
set aon_ury [expr $aon_lly_snap + $aon_height]

# Finally, create AON region
modifyPowerDomainAttr AON -box $aon_llx_snap $aon_lly_snap $aon_urx $aon_ury  -minGaps $polypitch_y $polypitch_y [expr $polypitch_x*6] [expr $polypitch_x*6]

