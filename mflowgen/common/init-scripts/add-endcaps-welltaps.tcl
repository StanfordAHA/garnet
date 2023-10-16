#=========================================================================
# add-endcaps-welltaps.tcl
#=========================================================================
# Author : 
# Date   : 
if {[info exists ADK_WELL_TAP_CELL] && [info exists ADK_WELL_TAP_INTERVAL]} {
  puts "Info: Found well-tap cell and interval in ADK, using it to add well taps"
  addWellTap -prefix TAP_2H \
             -cell [list ${ADK_WELL_TAP_CELL_2H}] \
             -cellInterval ${ADK_WELL_TAP_INTERVAL} \
             -incremental ${ADK_WELL_TAP_CELL_1H}

  addWellTap -prefix TAP_1H \
             -cell [list ${ADK_WELL_TAP_CELL_1H}] \
             -cellInterval ${ADK_WELL_TAP_INTERVAL} \
             -incremental ${ADK_WELL_TAP_CELL_2H}

  verifyWellTap -cell [list ${ADK_WELL_TAP_CELL_2H} ${ADK_WELL_TAP_CELL_1H}] \
                -report reports/welltap-1h2h.rpt \
                -rule   [ expr ${ADK_WELL_TAP_INTERVAL}/2 ]
}
