### Tool Settings
setDesignMode -process 16

set_interactive_constraint_modes [all_constraint_modes -active]

setDontUse IOA21D0BWP16P90 true
setDontUse IOA21D0BWP16P90LVT true
setDontUse IOA21D0BWP16P90ULVT true

setPlaceMode -checkImplantWidth true -honorImplantSpacing true -checkImplantMinArea true
setPlaceMode -honorImplantJog true -honor_implant_Jog_exception true

#setNanoRouteMode -drouteOnGridOnly {wire 4:7 via 3:6}
setNanoRouteMode -drouteOnGridOnly none
setNanoRouteMode -routeWithViaInPin {1:1}
setNanoRouteMode -routeTopRoutingLayer 9
setNanoRouteMode -routeBottomRoutingLayer 2
setNanoRouteMode -droutePostRouteSpreadWire false
setNanoRouteMode -dbViaWeight {*_P* -1}
setNanoRouteMode -routeExpAdvancedPinAccess true
setNanoRouteMode -routeExpAdvancedTechnology true
setNanoRouteMode -routeReserveSpaceForMultiCut false
setNanoRouteMode -routeWithSiDriven false
setNanoRouteMode -routeWithTimingDriven false
setNanoRouteMode -routeAutoPinAccessForBlockPin true
setNanoRouteMode -routeConcurrentMinimizeViaCountEffort high
setNanoRouteMode -droutePostRouteSwapVia false
setNanoRouteMode -routeExpUseAutoVia true
setNanoRouteMode -drouteExpAdvancedMarFix true
setMultiCpuUsage -localCpu 8
