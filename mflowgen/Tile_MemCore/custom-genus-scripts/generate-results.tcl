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
write_design -innovus -basename results_syn/syn_out
write_sdf -version "OVI 2.1" -recrem split -setuphold split > results_syn/syn_out.sdf
write_spef > results_syn/syn_out.spef
write_sdc -strict -view UNIFIED_BUFFER > results_syn/strict.sdc

write_name_mapping
