#=========================================================================
# pre_place.tcl
#=========================================================================
# This plug-in script is called before the corresponding Innovus flow step
#
# Author : Christopher Torng
# Date   : March 26, 2018

#-------------------------------------------------------------------------
# Example tasks include:
#          - Power planning related tasks which includes
#            - Power planning for power domains (ring/strap creations)
#            - Power Shut-off cell power hookup
#-------------------------------------------------------------------------

specifyCellPad *DFF* 2
reportCellPad -file $vars(rpt_dir)/$vars(step).cellpad.rpt

#-------------------------------------------------------------------------
# Global net connections for PG pins
#-------------------------------------------------------------------------

# Connect VNW / VPW if any cells have these pins

globalNetConnect VDD -type pgpin -pin VDD -inst *
globalNetConnect VDD -type tiehi
globalNetConnect VSS -type pgpin -pin VSS -inst *
globalNetConnect VSS -type tielo
globalNetConnect VDD -type pgpin -pin VPP -inst *
globalNetConnect VSS -type pgpin -pin VBB -inst *

#-------------------------------------------------------------------------
# Stdcell power rail preroute
#-------------------------------------------------------------------------
# Generate horizontal stdcell preroutes

sroute -nets {VDD VSS}

#-------------------------------------------------------------------------
# Implement power strategy
#-------------------------------------------------------------------------
# Older technologies use a single coarse power mesh, but more advanced
# technologies often use a combination of a fine+coarse power mesh.
#
# Here we check the direction of M2 to decide which power strategy to use.

set M2_direction [dbGet [dbGet head.layers.name 2 -p].direction]

if { $M2_direction == "Vertical" } {
  # Vertical M2 -- Use single power mesh strategy
  puts "Info: Using coarse-only power mesh because M2 is vertical"
  source $vars(plug_dir)/power_strategy_singlemesh.tcl
} else {
  # Horizontal M2 -- Use dual power mesh strategy
  puts "Info: Using fine+coarse power mesh because M2 is horizontal"
  source $vars(plug_dir)/power_strategy_dualmesh.tcl
}

#-------------------------------------------------------------------------
# Endcap and well tap specification
#-------------------------------------------------------------------------
# TSMC16 requires specification of different taps/caps for different
# locations/orientations, which the foundation flow does not natively support
source inputs/adk/adk.tcl
if {[expr ($ADK_END_CAP_CELL == "") && ($ADK_WELL_TAP_CELL == "")]} {
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
