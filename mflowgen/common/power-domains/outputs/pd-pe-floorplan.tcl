

#=========================================================================
# Create always-on domain region 
#=========================================================================

# AON Region Bounding Box
puts "##AON Region Bounding Box"
set offset     4.7
set aon_width  14
set aon_height 14

# Get all tech vars
source inputs/params.tcl

set aon_height_snap [expr ceil($aon_height/$polypitch_y)*$polypitch_y]
set aon_lx [expr $width/2 - $aon_width/2 + $offset -10 - 0.18]
set aon_lx_snap [expr ceil($aon_lx/$polypitch_x)*$polypitch_x]
set aon_ux [expr $width/2 + $aon_width/2 + $offset - 3]
set aon_ux_snap [expr ceil($aon_ux/$polypitch_x)*$polypitch_x]
modifyPowerDomainAttr AON -box $aon_lx_snap  [expr $height - $aon_height_snap - 10*$polypitch_y] $aon_ux_snap [expr $height - 10*$polypitch_y]  -minGaps $polypitch_y $polypitch_y [expr $polypitch_x*6] [expr $polypitch_x*6]

