# Tile_MemCore pre-route (lake-spec builds). Sourced by the route step after
# the postcts_hold design is restored, before run_route.tcl runs addFiller
# and `routeDesign -placementCheck`.
#
# GF12's smallest filler is 2 sites (no 1-site filler; the place step sets
# place_detail_legalization_inst_gap 2). A 1-site gap that legalization
# could not remove -- e.g. against a fixed tap/endcap or a macro halo --
# can't be filled, checkPlace reports FillerGap violations, and routeDesign
# refuses to route (NRIG-76). Seen on fw4_dw16_sc8192_dp_in4_out4_vc2 at
# 1.333 ns (5 unfilled sites, 99.99% density). -fitGap lets addFiller move a
# neighboring cell to close such gaps; it only acts where no filler fits.
if {[catch {setFillerMode -fitGap true} msg]} {
  puts "**WARN: pre-route: setFillerMode -fitGap unavailable ($msg); 1-site gaps may still stop routeDesign"
} else {
  puts "pre-route: setFillerMode -fitGap true"
}
