#=========================================================================
# add-welltaps-for-pad-latchup.tcl
#=========================================================================
# Author : 
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
                set welltap_area_lly $pad_lly
                set welltap_area_urx [expr $pad_urx + $ADK_LU_AFFECT_RANGE]
                set welltap_area_ury $pad_ury
            } else {
                set welltap_area_llx [expr $pad_llx - $ADK_LU_AFFECT_RANGE]
                set welltap_area_lly $pad_lly
                set welltap_area_urx $core_urx
                set welltap_area_ury $pad_ury
            }

            addWellTap -prefix LU_TAP_2H \
                       -area "$welltap_area_llx $welltap_area_lly $welltap_area_urx $welltap_area_ury" \
                       -cell [list ${ADK_WELL_TAP_CELL_2H}] \
                       -cellInterval $ADK_LU_WELLTAP_COVER_RANGE
        }
    }


