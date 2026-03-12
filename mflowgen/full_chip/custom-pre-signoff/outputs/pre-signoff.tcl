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

setMultiCpuUsage -localCpu 16 -remoteHost 1 -cpuPerRemoteHost 16
setSignoffOptMode -holdTargetSlack 0 -setupTargetSlack 0 -fixHoldAllowSetupOptimization true
signoffOptDesign -setup
signoffOptDesign -hold

deleteRouteBlk -all
verify_drc
ecoRoute -fix_drc

# # Sometimes we still have shorts, so delete the violating nets and reroute
editDeleteViolations
ecoRoute
