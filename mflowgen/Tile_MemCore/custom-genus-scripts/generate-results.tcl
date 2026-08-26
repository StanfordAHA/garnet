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
# write_design -innovus -basename results_syn/syn_out
write_design -basename results_syn/syn_out
write_sdf -version "OVI 2.1" -recrem split -setuphold split > results_syn/syn_out.sdf
write_spef > results_syn/syn_out.spef
write_sdc -strict -view UNIFIED_BUFFER > results_syn/strict.sdc

# Emit the RTL->gate name map so RTL-activity power (synopsys-ptpx-rtl) can
# `source` it to bind an RTL-sim SAIF onto the synthesized/routed netlist.
# Bare `write_name_mapping` only prints to the log -- redirect it to a file
# the synth step exports as design.namemap (see construct.py
# synth.extend_outputs). VALIDATE (build machine): confirm PrimeTime can
# `source` this file; if not, add the appropriate `-format`/`-style` flag for
# your Genus version so the output is PT-sourceable.
write_name_mapping > results_syn/design.namemap
