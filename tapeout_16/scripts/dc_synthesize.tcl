set lib /tsmc16/TSMCHOME
set timing_db [list /tsmc16/TSMCHOME/digital/Front_End/timing_power_noise/NLDM/tcbn16ffcllbwp16p90_100a/tcbn16ffcllbwp16p90ssgnp0p72vm40c.db] 
set techfile "$lib/digital/Back_End/milkyway/tcbn45gsbwp_110a/techfiles/HVH_0d5_0/tsmcn45_10lm7X2ZRDL.tf"
#set milkyway "/tsmc16/TSMCHOME/digital/Back_End/milkyway/tcbn16ffcllbwp16p90_100a"
set tluplus "/tsmc16/download/TECH16FFC/tluplus/cworst/Tech/cworst_CCworst_T/cln16ffc_1p9m_2xa1xd3xe2z_mim_ut-alrdl_cworst_CCworst_T.tluplus"
set layermap "$lib/digital/Back_End/milkyway/tcbn45gsbwp_110a/techfiles/tluplus/star.map_10M"
set design_name "PE"

#########################################################
lappend search_path . ..

#########################################################
# Define variables and setup libraries			#
#########################################################

read_db $timing_db;
read_db standard.sldb
set_app_var synthetic_library dw_foundation.sldb

set target_library $timing_db
set symbol_library "generic.sdb"
set mw_design_library mw_design_lib
#set mw_reference_library $milkyway
set mw_logic1_net VDD
set mw_logic0_net VSS
set mw_site_name_mapping {{core unit} {core7T unit} {core9T unit} {core12T unit} {bcore bunit} {bcore7T bunit} {bcore9T bunit} {bcore12T bunit}}
#create_mw_lib $mw_design_library -technology $techfile -mw_reference_library $mw_reference_library -open
#set_tlu_plus_files -max_tluplus $tluplus -tech2itf_map $layermap
#check_tlu_plus_files

while {[get_license {"DesignWare"}] == 0} {
  echo {Waiting for DesignWare license...}
  sh sleep 120
}
set synlib_wait_for_design_license {"DesignWare"}
set synlib_abort_wo_dw_license true
set synthetic_library dw_foundation.sldb
set link_library [concat $timing_db * standard.sldb dw_foundation.sldb]

lappend search_path [format "%s%s" $synopsys_root {/dw/sim_ver}]
read_db dw_foundation.sldb


# Get DC-Ultra license
while {[get_license {"DC-Ultra-Opt"}] == 0} {
  echo {Waiting for DC-Ultra license...}
  sh sleep 120
}

# Settings for XG mode compatibility issues
set uniquify_keep_original_design true
set ungroup_keep_original_design true

# Compile optimization settings
set compile_seqmap_identify_shift_registers false
set compile_seqmap_propagate_constants true
set compile_retime_exception_registers true
set compile_enable_constant_propagation_with_no_boundary_opt true
set case_analysis_with_logic_constants true
set timing_use_enhanced_capacitance_modeling true

# Presto Verilog optimization settings
set hdlin_reporting_level comprehensive
set hdlin_check_no_latch true
set hdlin_vrlg_std 2001
set hdlin_mux_size_limit 32
set hdlin_optimize_pla_effort 3
set hdlin_auto_save_templates true
set hdl_keep_licenses false

# Reset related optimization settings
set compile_seqmap_sync_clr_preset_more_opt true
set hdlin_ff_always_sync_set_reset true

# Misc
define_design_lib WORK -path workdir
sh mkdir -p workdir
suppress_message [list TIM-052 TIM-128 ELAB-311 VER-173 PSYN-1002 TFCHK-014 HDL-193 RCEX-011]
set verbose_messages false
set sh_new_variable_message false
set verilogout_no_tri true
set report_default_significant_digits 3
set exit_delete_command_log_file true
set exit_delete_filename_log_file true
set write_sdc_output_net_resistance false
set write_sdc_output_lumped_net_capacitance false
set test_disable_enhanced_dft_drc_reporting false
set monitor_cpu_memory true

# Tool workarounds
set_multicore_feature -disable 1

#########################################################
# Read in design					#
#########################################################
puts "@file_info: Redirecting to /dev/null..."
redirect /dev/null {remove_license HDL-Compiler}
while {[get_license {"HDL-Compiler"}] == 0} {
   echo {Waiting for HDL-Compiler license...}
   sh sleep 120
}

read_file -rtl [list ../../genesis_verif/garnet.sv]

current_design $design_name

set LINK_STATUS [link]
if {$LINK_STATUS == 0} {
  echo [concat [format "%s%s" [join [concat "Err" "or"] ""] {: unresolved references. Exiting ...}]]
  quit
}

redirect /dev/null {remove_license HDL-Compiler}

report_timing -loops -enable_preset_clear_arcs -nosplit

current_design $design_name
uniquify
set_fix_multiple_port_nets -all -buffer_constants
set_map_only {gtech/GTECH_ADD_ABC gtech/GTECH_ADD_AB gtech/GTECH_MUX4 gtech/GTECH_MUX2} true

#########################################################
# Constraints                                           #
#########################################################
create_clock -name clk -period 2.3 [get_ports CLK]
set_input_delay -max 0.2 -clock clk [all_inputs]
set_output_delay -max 0.2 -clock clk [all_outputs]
set_input_delay -min 0 -clock clk [all_inputs]
set_output_delay -min 0 -clock clk [all_outputs]

set_input_transition 0.2 [all_inputs]

# the PE instruction is static
set_false_path -through [get_ports {inst*}]  -to [all_outputs]


set_attribute [get_lib_cells {*/E* */G* */*D0* */*D1* */*D2* */*D3* */*D16* */*D20* */*D24* */*D28* */*D32* */*SDF* */*DFM*}] dont_use true
#########################################################
# Top-level full compile				#
#########################################################

uniquify
#set_dont_touch [get_nets *]
#compile_ultra -timing_high_effort_script -no_autoungroup
compile_ultra -timing_high_effort_script

report_timing -loops -enable_preset_clear_arcs -nosplit
uniquify

ungroup -flatten -all -force
#compile_ultra -area_high_effort_script -no_autoungroup
compile_ultra -area_high_effort_script

#########################################################
# Generate output files					#
#########################################################

current_design $design_name
ungroup -flatten -all -force
change_names -rules verilog -hier
write -hier -f verilog -o rtl_syn.v
redirect rtl_syn.timing {eval report_timing -nets -max_paths 1000 -nworst 10 -unique_pins -nosplit}
redirect rtl_syn.qor {report_qor}
redirect rtl_syn.area {report_area -physical -hierarchy -designware -nosplit}
write_sdc rtl_syn.sdc -nosplit
write_parasitics -script -format reduced -output rtl_syn.setload
quit
