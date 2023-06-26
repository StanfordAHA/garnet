#=========================================================================
# create-rows.tcl
#=========================================================================
# Author : 
# Date   : 

# delete existing rows
deleteRow -all

# create single height rows for stdcells/ECO cells
createRow -site $ADK_CORE_SINGLE_HEIGHT     -flip1st
createRow -site $ADK_CORE_SINGLE_HEIGHT_ECO -flip1st

# create double height rows for well tap cells
set pitch_x [dbGet top.fPlan.coreSite.size_x]
set pitch_y [dbGet top.fPlan.coreSite.size_y]
set fplan_urx [dbGet top.fPlan.box_urx]
set fplan_ury [dbGet top.fPlan.box_ury]
set core_llx [expr $pitch_x * $ADK_WHITE_SPACE_FACTOR_HORI]
set core_lly [expr $pitch_y * $ADK_WHITE_SPACE_FACTOR_VERT]
set core_urx [expr $fplan_urx - $core_llx]
set core_ury [expr $fplan_ury - $core_lly]
createRow -site $ADK_CORE_DOUBLE_HEIGHT -noFlip \
    -area "$core_llx $core_lly $core_urx $core_ury"
