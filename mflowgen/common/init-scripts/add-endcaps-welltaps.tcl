#=========================================================================
# add-endcaps-welltaps.tcl
#=========================================================================
# Author : 
# Date   : 
if {[info exists ADK_WELL_TAP_CELL] && [info exists ADK_WELL_TAP_INTERVAL]} {
  puts "Info: Found well-tap cell and interval in ADK, using it to add well taps"
  specifyCellEdgeSpacing tap1 tap1 ${ADK_WELL_TAP_INTERVAL}
  specifyCellEdgeType -cell ${ADK_WELL_TAP_CELL} -left tap1
  specifyCellEdgeType -cell ${ADK_WELL_TAP_CELL} -right tap1
  
  addWellTap -cell [list ${ADK_WELL_TAP_CELL}] \
             -prefix       TAP_2H \
             -cellInterval ${ADK_WELL_TAP_INTERVAL}
  
  verifyWellTap -cell [list ${ADK_WELL_TAP_CELL}] \
                -report reports/welltap.rpt \
                -rule   [ expr ${ADK_WELL_TAP_INTERVAL}/2 ]
  
  deleteCellEdgeSpacing tap1 tap1
}
