# Flowkit v0.2
################################################################################
# This file contains content which is used to customize the refererence flow
# process.  Commands such as 'create_flow', 'create_flow_step' and 'edit_flow'
# would be most prevalent.  For example:
#
# create_flow_step -name write_sdf {
#   write_sdf [get_db flow_report_directory]/[get_db local_flow].sdf
# }
#
# edit_flow -after flow_step:innovus_report_late_timing -append flow_step:write_sdf
#
################################################################################

################################################################################
# FLOW CUSTOMIZATIONS / FLOW STEP ADDITIONS
################################################################################

source /tools/projects/stevo/craft/fft2-chip/vlsi/flow/scripts/common_vars.tcl;# FOOBAR

##############################################################################
# STEP report_late_paths
##############################################################################
create_flow_step -name report_late_paths -skip_db -exclude_time_metric -owner cadence {
  #- Reports that show detailed timing with Graph Based Analysis (GBA)
  report_timing -max_paths 500 -nworst 1 -path_type endpoint        > [get_db flow_report_directory]/[get_db flow_report_name]/setup.endpoint.rpt
  report_timing -max_paths 1   -nworst 1 -path_type full_clock -net > [get_db flow_report_directory]/[get_db flow_report_name]/setup.worst.rpt
  report_timing -max_paths 500 -nworst 1 -path_type full_clock      > [get_db flow_report_directory]/[get_db flow_report_name]/setup.gba.rpt

  #- Reports that show detailed timing with Path Based Analysis (PBA)
  if {[is_flow -inside flow:sta]} {
    report_timing -max_paths 50 -nworst 1 -path_type full_clock -retime path_slew_propagation > [get_db flow_report_directory]/[get_db flow_report_name]/setup.pba.rpt
  }
}

##############################################################################
# STEP report_early_paths
##############################################################################
create_flow_step -name report_early_paths -skip_db -exclude_time_metric -owner cadence {
  #- Reports that show detailed early timing with Graph Based Analysis (GBA)
  report_timing -early -max_paths 500 -nworst 1 -path_type endpoint        > [get_db flow_report_directory]/[get_db flow_report_name]/hold.endpoint.rpt
  report_timing -early -max_paths 1   -nworst 1 -path_type full_clock -net > [get_db flow_report_directory]/[get_db flow_report_name]/hold.worst_max_path.rpt
  report_timing -early -max_paths 500 -nworst 1 -path_type full_clock      > [get_db flow_report_directory]/[get_db flow_report_name]/hold.gba.rpt

  #- Reports that show detailed timing with Path Based Analysis (PBA)
  if {[is_flow -inside flow:sta]} {
    report_timing -early -max_paths 50 -nworst 1 -path_type full_clock -retime path_slew_propagation  > [get_db flow_report_directory]/[get_db flow_report_name]/hold.pba.rpt
  }
}

##############################################################################
# STEP genus_to_lec
##############################################################################
create_flow_step -name genus_to_lec -skip_db -owner cadence {
  #- create output location
  set design  [get_db [current_design] .name]
  set out_dir [file join [get_db flow_database_directory] [get_db flow_report_name]]
  file mkdir $out_dir

  #- write design and library information
  write_hdl -lec > [file join $out_dir $design.lec]

  #- write dofile for LEC
  write_lec_script \
    -logfile [file join [get_db flow_log_directory] lec.[get_db flow_report_name].log] \
    -top $design \
    -revised_design [file join $out_dir $design.lec] \
    > [file dirname [get_db verification_directory_naming_style]]/lec.[get_db flow_report_name].do
    #<< PLACEHOLDER: LEC SCRIPT OPTIONS >> \

  #- schedule the LEC flow
  schedule_flow \
    -flow lec \
    -branch [get_db flow_report_name] \
    -no_db \
    -no_sync \
    -tool_options "-nogui -lpgxl -do [file dirname [get_db verification_directory_naming_style]]/lec.[get_db flow_report_name].do"
}

##############################################################################
# STEP read_parasitics
##############################################################################
create_flow_step -name read_parasitics -skip_db -exclude_time_metric -owner cadence {
  #- initialize annotations using spef
#  read_parasitics         << PLACEHOLDER: PARASITIC LOAD OPTIONS >>
}


################################################################################
# FLOW CUSTOMIZATIONS
################################################################################
#- Library and Design data pointers
if {! [is_attribute gds_files -obj_type root]} {
  define_attribute gds_files -obj_type root -data_type string -category flow
}
if {! [is_attribute lib_dir -obj_type root]} {
  define_attribute lib_dir -obj_type root -data_type string -category flow
}
if {! [is_attribute TSMC_gds_map -obj_type root]} {
  define_attribute TSMC_gds_map -obj_type root -data_type string -category flow
}
if {! [is_attribute core -obj_type root]} {
  define_attribute core -obj_type root -data_type string -category flow
}
if {! [is_attribute flow_source_directory -obj_type root]} {
  define_attribute flow_source_directory -obj_type root -data_type string -category flow
}
if {! [is_attribute TSMC_wellTapInterval -obj_type root]} {
  define_attribute  TSMC_wellTapInterval -obj_type root -data_type string -category flow
}
if {! [is_attribute tech -obj_type root]} {
  define_attribute tech -obj_type root -data_type string -category flow
}
if {! [is_attribute rtl -obj_type root]} {
  define_attribute rtl -obj_type root -data_type string -category flow
}
if {! [is_attribute constraints_files -obj_type root]} {
  define_attribute constraints_files -obj_type root -data_type string -category flow
}
if {! [is_attribute power_files -obj_type root]} {
  define_attribute power_files -obj_type root -data_type string -category flow
}
if {! [is_attribute io_file -obj_type root]} {
  define_attribute io_file -obj_type root -data_type string -category flow
}

set_db core                     "$CORE"
set_db tech                     "$TECH_DIR"
set_db flow_source_directory    "$SCRIPTS_DIR"
set_db constraints_files        "$CONSTRAINTS"
set_db power_files              "$POWER_FILES"
set_db rtl                      "$RTL"
set_db io_file                  "$IOFILE"

set_db lib_dir                  "$env(TSMCHOME)/digital"
set_db gds_files                "[glob [get_db tech]/gds/*]"
set_db TSMC_gds_map             "/tools/projects/stevo/craft/fft2-chip/vlsi/flow/scripts/gds.map"

#########################################################
### running single mode through Genus
#########################################################
create_flow_step -name change_view -skip_db -owner CRAFT {
  if { [regexp {mmmc} [get_db flow_run_tag]] } {
    puts "CRAFT-404 adding additional modes at placement"
    set_analysis_view -setup [get_db analysis_views .name *setup*] -hold [get_db analysis_views .name *hold*]
  }
}


# [stevo]: fixes to min pulse width bug


create_flow_step -name adjust_clock_spec -skip_db -owner CRAFT {                                               
  puts "CRAFT-404 reload modified clock spec "
  delete_skew_groups clkout_32_0/func
  delete_skew_groups clkout_32_1/func
  delete_skew_groups clkout_32_6/func
  delete_skew_groups clkout_32_9/func
  delete_skew_groups clkout_32_12/func
  delete_skew_groups clkout_32_19/func
  delete_skew_groups clkout_27_0/func
  delete_skew_groups clkout_27_1/func
  delete_skew_groups clkout_27_6/func
  delete_skew_groups clkout_27_9/func
  delete_skew_groups clkout_27_12/func
  delete_skew_groups clkout_27_19/func
  delete_skew_groups clkout_25_0/func
  delete_skew_groups clkout_25_1/func
  delete_skew_groups clkout_25_6/func
  delete_skew_groups clkout_25_9/func
  delete_skew_groups clkout_25_12/func
  delete_skew_groups clkout_25_19/func
}
edit_flow -after flow_step:add_clock_spec -append flow_step:adjust_clock_spec        


create_flow_step -name reset_clock_latency -skip_db -owner CRAFT {
  puts "CRAFT-404 resetting clock latency "                                          
  set_interactive_constraint_modes [all_constraint_modes -active]     
  reset_clock_latency  [all_clocks]
}
edit_flow -before flow_step:add_clock_spec -append flow_step:reset_clock_latency


