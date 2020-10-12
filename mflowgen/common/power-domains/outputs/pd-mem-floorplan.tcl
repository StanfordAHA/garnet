
#=========================================================================
# Create always-on domain region 
#=========================================================================


#Dont dont_touch constraints
source inputs/dont-touch-constraints.tcl

# create always on domain region
   ##AON Region Bounding Box
   puts "##AON Region Bounding Box"
   set offset 7.1
   set aon_width 14
   set aon_height 11
   
   set polypitch_y [dbGet top.fPlan.coreSite.size_y]
   set polypitch_x [dbGet top.fPlan.coreSite.size_x] 
   
   set aon_height_snap [expr ceil($aon_height/$polypitch_y)*$polypitch_y]
   set aon_lx [expr $width * 0.15 - $aon_width/2 + $offset - 0.18]
   set aon_lx_snap [expr ceil($aon_lx/$polypitch_x)*$polypitch_x]
   set aon_ux [expr $width * 0.15 + $aon_width/2 + $offset - 3]
   set aon_ux_snap [expr ceil($aon_ux/$polypitch_x)*$polypitch_x]
   modifyPowerDomainAttr AON -box $aon_lx_snap  [expr $height - $aon_height_snap - 10*$polypitch_y] $aon_ux_snap [expr $height - 10*$polypitch_y]  -minGaps $polypitch_y $polypitch_y [expr $polypitch_x*6] [expr $polypitch_x*6]




