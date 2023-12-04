#=========================================================================
# add-welltaps-for-pad-latchup.tcl
#=========================================================================
# If standard cells are placed too close to the diodes inside the pads, it
# will result in Latch Up (LU) DRC violation. To fix this, we can either:
#     1. increase the distance between the pads and the standard cells
#     2. add welltaps close to the standard cells to protect them
# If the chip area is not a concern, we can use option 1. Otherwise, we can
# use the add-welltaps-for-pad-latchup.tcl script to add welltaps.
# Author : Po-Han Chen
# Date   : 

set core_llx [dbGet top.fPlan.coreBox_llx]
set core_lly [dbGet top.fPlan.coreBox_lly]
set core_urx [dbGet top.fPlan.coreBox_urx]
set core_ury [dbGet top.fPlan.coreBox_ury]

foreach side {left right} {

    if {$side == "left"} {
        set welltap_area_llx [expr $core_llx]
        set welltap_area_lly [expr $core_lly]
        set welltap_area_urx [expr $core_llx + $ADK_LU_AFFECT_RANGE]
        set welltap_area_ury [expr $core_ury]
    } else {
        set welltap_area_llx [expr $core_urx - $ADK_LU_AFFECT_RANGE]
        set welltap_area_lly [expr $core_lly]
        set welltap_area_urx [expr $core_urx]
        set welltap_area_ury [expr $core_ury]
    }

    addWellTap -prefix LU_TAP_2H \
               -area "$welltap_area_llx $welltap_area_lly $welltap_area_urx $welltap_area_ury" \
               -cell [list ${ADK_WELL_TAP_CELL_2H}] \
               -cellInterval $ADK_LU_WELLTAP_COVER_RANGE
        
}