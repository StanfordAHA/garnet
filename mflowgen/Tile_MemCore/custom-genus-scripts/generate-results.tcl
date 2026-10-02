#=========================================================================
# generate-results.tcl
#=========================================================================
# Write Genus results.
#
# Author : Alex Carsello, James Thomas
# Date   : July 14, 2020

if { $uniquify_with_design_name == True } {
  update_names -subdesign -force -prefix ${design_name}_
}

write_snapshot -directory results_syn -tag final

# Top-100 worst setup paths, one per endpoint (write_snapshot's
# final_time.rpt stops at 50): full paths + a one-line-per-path summary.
# This step runs Genus in the LEGACY UI (designer-interface.tcl sets
# common_ui false), so it is `report timing -num_paths`; the common-UI
# `report_timing -max_paths` errors here (checked on Genus 19.10/20.11).
# catch: a report must never fail synthesis.
file mkdir reports
if {[catch {report timing -num_paths 100 > reports/${design_name}.timing.setup.top100.rpt} err]} {
  puts "WARNING: generate-results: top-100 timing report failed: $err"
}
if {[catch {report timing -num_paths 100 -summary > reports/${design_name}.timing.setup.top100.summary.rpt} err]} {
  puts "WARNING: generate-results: top-100 timing summary failed: $err"
}

# write_design -innovus -basename results_syn/syn_out
write_design -basename results_syn/syn_out
write_sdf -version "OVI 2.1" -recrem split -setuphold split > results_syn/syn_out.sdf
write_spef > results_syn/syn_out.spef
write_sdc -strict -view UNIFIED_BUFFER > results_syn/strict.sdc

# Emit the RTL->gate name map (name_map.rpt) so RTL-activity power
# (synopsys-ptpx-rtl) can `source` it to bind an RTL-sim SAIF onto the gate
# netlist. Bare write_name_mapping writes name_map.rpt, which the
# cadence-genus-synthesis step already links to its design.namemap output
# (mflowgen/nodes/cadence-genus-synthesis/configure.yml).
write_name_mapping
