#=========================================================================
# edge-blockages.tcl
#=========================================================================
# This script creates thin routing blockages around the edge of
# the design in order to prevent DRCs that occur when the block is
# integrated into another design, or abutted with another block.
#
# NOTE: This script must be run after pins are assigned. Otherwise,
# the blockage will block the pins from being placed
#
# Author : Alex Carsello
# Date   : April 29, 2020

# Get design size
set ury [dbGet top.fPlan.box_ury]
set urx [dbGet top.fPlan.box_urx]

# Set thickness of blockage
# This must be less then pin width. Otherwise, the pins will be inaccessible
set blockage_width 0.3

createRouteBlk -name bottom -exceptpgnet -layer all -box 0 0 $urx $blockage_width
createRouteBlk -name right -exceptpgnet -layer all -box [expr $urx - $blockage_width] 0 $urx $ury
createRouteBlk -name top -exceptpgnet -layer all -box 0 [expr $ury - $blockage_width] $urx $ury
createRouteBlk -name left -exceptpgnet -layer all -box 0 0 $blockage_width $ury
