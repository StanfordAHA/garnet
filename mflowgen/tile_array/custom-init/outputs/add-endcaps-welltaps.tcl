#=========================================================================
# add-endcaps-welltaps.tcl
#=========================================================================
# Author : 
# Date   : 

#-------------------------------------------------------------------------
# Endcap and well tap specification
#-------------------------------------------------------------------------
# TSMC16 requires specification of different taps/caps for different
# locations/orientations, which the foundation flow does not natively support

if {[expr {$ADK_END_CAP_CELL == ""} && {$ADK_WELL_TAP_CELL == ""}]} {
  adk_set_end_cap_mode
  adk_set_well_tap_mode
  adk_add_end_caps
  adk_add_well_taps
}

#setPlaceMode -checkImplantWidth true -honorImplantSpacing true -checkImplantMinArea true
#setPlaceMode -honorImplantJog true -honor_implant_Jog_exception true

#setNanoRouteMode -drouteOnGridOnly {wire 4:7 via 3:6}
#setNanoRouteMode -routeWithViaInPin {1:1}
#setNanoRouteMode -routeTopRoutingLayer $max_route_layer($design)
#setNanoRouteMode -routeBottomRoutingLayer 2
#setNanoRouteMode -droutePostRouteSpreadWire false
#setNanoRouteMode -dbViaWeight {*_P* -1}
#setNanoRouteMode -routeExpAdvancedPinAccess true
#setNanoRouteMode -routeExpAdvancedTechnology true
#setNanoRouteMode -routeReserveSpaceForMultiCut false
#setNanoRouteMode -routeWithSiDriven false
#setNanoRouteMode -routeWithTimingDriven false
#setNanoRouteMode -routeAutoPinAccessForBlockPin true
#setNanoRouteMode -routeConcurrentMinimizeViaCountEffort high
#setNanoRouteMode -droutePostRouteSwapVia false
#setNanoRouteMode -routeExpUseAutoVia true
#setNanoRouteMode -drouteExpAdvancedMarFix true

# SR 09/2019 - limit optimization iterations to TEN only
# setNanoRouteMode -drouteEndIteration 10
#
#set_clock_uncertainty -hold 0.04 -from clk -to clk
#set_clock_uncertainty -setup 0.04 -from clk -to clk

#setOptMode -enableDataToDataChecks true -addAOFeedThruBuffer true


