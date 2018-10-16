set timing_db "/nobackup/jbrunhav/synopsys_EDK2/synopsys_EDK2/TSMCHOME/digital/Front_End/timing_power_noise/NLDM/tcbn45gsbwp_110a/tcbn45gsbwpwcl.db"
set techfile "/nobackup/jbrunhav/synopsys_EDK2/synopsys_EDK2/TSMCHOME/digital/Back_End/milkyway/tcbn45gsbwp_110a/techfiles/HVH_0d5_0/tsmcn45_10lm7X2ZRDL.tf"
set milkyway "/nobackup/jbrunhav/synopsys_EDK2/synopsys_EDK2/TSMCHOME/digital/Back_End/milkyway/tcbn45gsbwp_110a/frame_only_HVH_0d5_0/tcbn45gsbwp"
set tluplus "/nobackup/jbrunhav/synopsys_EDK2/synopsys_EDK2/TSMCHOME/digital/Back_End/milkyway/tcbn45gsbwp_110a/techfiles/tluplus/cln45gs_1p10m+alrdl_cworst_top2.tluplus"
set layermap "/nobackup/jbrunhav/synopsys_EDK2/synopsys_EDK2/TSMCHOME/digital/Back_End/milkyway/tcbn45gsbwp_110a/techfiles/tluplus/star.map_10M"
set design_name "regfile"
set rtl_files "pnr.v"
set SETLOAD "pnr.setload"
set LIBNAME $design_name
###########################################################################################################
lappend search_path . ..
set link_path "* $timing_db"

#########################################################
# Define variables and setup libraries			#
#########################################################

read_db $timing_db;

#########################################################
# Read in design					#
#########################################################
read_verilog $rtl_files

set LINK_STATUS [link]
if {$LINK_STATUS == 0} {
  echo [concat [format "%s%s" [join [concat "Err" "or"] ""] {: unresolved references. Exiting ...}]]
  quit
}

current_design $design_name

#########################################################
# Constraints                                          #
#########################################################

source $SETLOAD 
create_clock -name clk -period 5 -waveform {0 2.50} [get_ports clk]
set_input_delay 0.0 -clock clk [all_inputs]
set_output_delay 0.0 -clock clk [all_outputs]

#########################################################
# Read VCD                                              #
#########################################################

while {[get_license {"PrimeTime-PX"}] == 0} {
  echo {Waiting for PrimeTime-PX license...}
  sh sleep 120
}

set power_enable_analysis true
set power_analysis_mode averaged
set power_clock_network_include_clock_gating_network true
set power_clock_network_include_register_clock_pin_power true
set power_enable_multi_rail_analysis true
set power_limit_extrapolation_range true

#########################################################
# Iterate over switching activity files to generate     #
# average or time based power reports per diag          #
#########################################################

update_timing -full
read_vcd verilog.vcd -strip_path "tb/dut"
update_power
set a 0; foreach_in_collection c [get_cells *] {set a [expr $a + [get_attribute $c area]]}
redirect pnr.area {echo $a}

report_power -verbose > power.rpt
extract_model -output $LIBNAME -format {lib} -library_cell -remove_internal_arcs
quit
