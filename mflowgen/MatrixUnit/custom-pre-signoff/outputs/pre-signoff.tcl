#=========================================================================
# pre-signoff.tcl
#=========================================================================
# Description:
# This script is used to fix a small number of DRC errors at the end of
# the design flow. It performs DRC verification, deletes violating nets,
# and reroutes them to resolve issues.
#
# Note:
# This script can be skipped if there are no DRC errors at signoff.
#=========================================================================

# deleteRouteBlk -all

verify_drc
ecoRoute -fix_drc

# # Sometimes we still have shorts, so delete the violating nets and reroute
editDeleteViolations
ecoRoute

# delete problematic wires
selectWire 1117.2380 0.0000 1117.2820 2862.0000 5 VDD
editCutWire -selected -line { 1117.2045 2607.1105 1117.3255 2607.1105 }
selectWire 1117.2380 2607.1105 1117.2820 2862.0000 5 VDD
editCutWire -selected -line { 1117.2245 2833.9105 1117.3165 2833.9105 }
editSelect -area { 1117.2 2607.09 1117.33 2833.9245 } -layer {v4 m5 v5} -net {VDD} -object_type {Wire Via}
deleteSelectedFromFPlan

# fix the god damn LVS error
update_names -restricted {:} -replace_str "_"
