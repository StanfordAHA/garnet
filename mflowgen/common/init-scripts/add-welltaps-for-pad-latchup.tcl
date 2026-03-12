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
        set pad_objs [dbGet -p top.insts.name IOPAD_$side*]
        foreach pad_obj $pad_objs {
            set pad_llx [dbGet $pad_obj.box_llx]
            set pad_lly [dbGet $pad_obj.box_lly]
            set pad_urx [dbGet $pad_obj.box_urx]
            set pad_ury [dbGet $pad_obj.box_ury]

            if {$side == "left"} {
                set welltap_area_llx $core_llx
                set welltap_area_lly [expr $pad_lly - 16.2]
                set welltap_area_urx [expr $pad_urx + $ADK_LU_AFFECT_RANGE]
                set welltap_area_ury [expr $pad_ury + 16.2]
            } else {
                set welltap_area_llx [expr $pad_llx - $ADK_LU_AFFECT_RANGE]
                set welltap_area_lly [expr $pad_lly - 16.2]
                set welltap_area_urx $core_urx
                set welltap_area_ury [expr $pad_ury + 16.2]
            }

            addWellTap -prefix LU_TAP_2H \
                       -area "$welltap_area_llx $welltap_area_lly $welltap_area_urx $welltap_area_ury" \
                       -cell [list ${ADK_WELL_TAP_CELL_2H}] \
                       -cellInterval $ADK_LU_WELLTAP_COVER_RANGE
        }
    }

# set pad_llx 22.68
# set pad_lly 3632.58
# set pad_urx 68.04 
# set pad_ury 3733.38
# set welltap_area_llx $core_llx
# set welltap_area_lly [expr $pad_lly - 0.54]
# set welltap_area_urx [expr $pad_urx + $ADK_LU_AFFECT_RANGE]
# set welltap_area_ury [expr $pad_ury + 0.54]
# addWellTap -prefix LU_TAP_2H \
#                            -area "$welltap_area_llx $welltap_area_lly $welltap_area_urx $welltap_area_ury" \
#                            -cell [list ${ADK_WELL_TAP_CELL_2H}] \
#                            -cellInterval $ADK_LU_WELLTAP_COVER_RANGE

# set pad_llx 22.68
# set pad_lly 3480.12
# set pad_urx 68.04
# set pad_ury 3577.14
# set welltap_area_llx $core_llx
# set welltap_area_lly [expr $pad_lly - 0.54]
# set welltap_area_urx [expr $pad_urx + $ADK_LU_AFFECT_RANGE]
# set welltap_area_ury [expr $pad_ury + 0.54]
# addWellTap -prefix LU_TAP_2H \
#                            -area "$welltap_area_llx $welltap_area_lly $welltap_area_urx $welltap_area_ury" \
#                            -cell [list ${ADK_WELL_TAP_CELL_2H}] \
#                            -cellInterval $ADK_LU_WELLTAP_COVER_RANGE

# set pad_llx 22.68
# set pad_lly 3318.84
# set pad_urx 68.04
# set pad_ury 3422.16
# set welltap_area_llx $core_llx
# set welltap_area_lly [expr $pad_lly - 0.54]
# set welltap_area_urx [expr $pad_urx + $ADK_LU_AFFECT_RANGE]
# set welltap_area_ury [expr $pad_ury + 0.54]
# addWellTap -prefix LU_TAP_2H \
#                            -area "$welltap_area_llx $welltap_area_lly $welltap_area_urx $welltap_area_ury" \
#                            -cell [list ${ADK_WELL_TAP_CELL_2H}] \
#                            -cellInterval $ADK_LU_WELLTAP_COVER_RANGE

# set pad_llx 22.68
# set pad_lly 3162.6
# set pad_urx 68.04
# set pad_ury 3265.92
# set welltap_area_llx $core_llx
# set welltap_area_lly [expr $pad_lly - 0.54]
# set welltap_area_urx [expr $pad_urx + $ADK_LU_AFFECT_RANGE]
# set welltap_area_ury [expr $pad_ury + 0.54]
# addWellTap -prefix LU_TAP_2H \
#                            -area "$welltap_area_llx $welltap_area_lly $welltap_area_urx $welltap_area_ury" \
#                            -cell [list ${ADK_WELL_TAP_CELL_2H}] \
#                            -cellInterval $ADK_LU_WELLTAP_COVER_RANGE

set welltap_area_llx 3840.48
set welltap_area_urx 3849.336
set welltap_area_lly 3282.12
set welltap_area_ury 3302.64
addWellTap -prefix LU_TAP_2H \
                           -area "$welltap_area_llx $welltap_area_lly $welltap_area_urx $welltap_area_ury" \
                           -cell [list ${ADK_WELL_TAP_CELL_2H}] \
                           -cellInterval $ADK_LU_WELLTAP_COVER_RANGE

set welltap_area_llx 3840.48
set welltap_area_urx 3849.336
set welltap_area_lly 3437.64
set welltap_area_ury 3463.56
addWellTap -prefix LU_TAP_2H \
                           -area "$welltap_area_llx $welltap_area_lly $welltap_area_urx $welltap_area_ury" \
                           -cell [list ${ADK_WELL_TAP_CELL_2H}] \
                           -cellInterval $ADK_LU_WELLTAP_COVER_RANGE

set welltap_area_llx 3840.48
set welltap_area_urx 3849.336
set welltap_area_lly 3593.16
set welltap_area_ury 3616.92
addWellTap -prefix LU_TAP_2H \
                           -area "$welltap_area_llx $welltap_area_lly $welltap_area_urx $welltap_area_ury" \
                           -cell [list ${ADK_WELL_TAP_CELL_2H}] \
                           -cellInterval $ADK_LU_WELLTAP_COVER_RANGE

