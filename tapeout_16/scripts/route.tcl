
### Tool Settings
setDesignMode -process 16

set_interactive_constraint_modes [all_constraint_modes -active]

setNanoRouteMode -drouteOnGridOnly {wire 4:7 via 3:6}
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


#### Route Design
routeDesign
optDesign -postRoute
