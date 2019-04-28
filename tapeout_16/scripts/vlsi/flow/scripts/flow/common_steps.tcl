# Flowkit v0.2
#- common_steps.tcl : defines common flow attributes and flowsteps

#===============================================================================
# Common attributes used in implementation flow
#===============================================================================

#- Specify Flow Header (runs at the start of run_flow command)
set_db flow_header_tcl {
  #- Set the report name based on the lowest flow name contained in the trunk flow
  if {[regexp {block_start|hier_start} [get_db flow_step_current]]} {
    set_db flow_report_name [get_db [lindex [get_db flow_hier_path] end] .name]
  }

  #- Load Feature Specified Attributes and Overrides
  uplevel #0 source [file join [get_db flow_source_directory] [get_db program_short_name]_config.tcl]
}

#- Specify Flow Footer (runs at the conclusion of run_flow command)
set_db flow_footer_tcl {
  #- Write the html run summary
  report_metric \
    -file [get_db flow_report_directory]/qor.html \
    -format html
}

#===============================================================================
# Common steps used in implementation flow
#===============================================================================

##############################################################################
# STEP block_start
##############################################################################
create_flow_step -name block_start -skip_db -owner cadence {
  #- Create report dir (if necessary)
  file mkdir [file normalize [file join [get_db flow_report_directory] [get_db flow_report_name]]]

  #- Store non-default root attributes to metrics
  set flow_root_config [report_obj -tcl]
  foreach key [dict keys $flow_root_config] {
    if {[string length [dict get $flow_root_config $key]] > 200} {
      dict set flow_root_config $key "\[long value truncated\]"
    }
  }
  set_metric -name flow.root_config -value $flow_root_config
}

##############################################################################
# STEP block_finish
##############################################################################
create_flow_step -name block_finish -owner cadence {
  #- Make sure flow_report_name is reset from any reports executed during the flow
  set_db flow_report_name [get_db [lindex [get_db flow_hier_path] end] .name]
}

#===============================================================================
# Common steps used in reporting
#===============================================================================

##############################################################################
# STEP report_start
##############################################################################
create_flow_step -name report_start -skip_db -exclude_time_metric -owner cadence {
  #- Create report dir (if necessary)
  file mkdir [file normalize [file join [get_db flow_report_directory] [get_db flow_report_name]]]
}

##############################################################################
# STEP report_finish
##############################################################################
create_flow_step -name report_finish -skip_db -exclude_time_metric -owner cadence {
}

##############################################################################
# STEP signoff_start
##############################################################################
create_flow_step -name signoff_start -skip_db -owner cadence {
  set_db flow_report_name [get_db flow_report_name].signoff

  #- Create report dir (if necessary)
  file mkdir [file normalize [file join [get_db flow_report_directory] [get_db flow_report_name]]]
}

##############################################################################
# STEP signoff_finish
##############################################################################
create_flow_step -name signoff_finish -skip_db -owner cadence {
}

##############################################################################
# STEP innovus_to_tempus
##############################################################################
create_flow_step -name innovus_to_tempus -skip_db -owner cadence {
  #- create output location
  set design  [get_db [current_design] .name]
  set out_dir [file join [get_db flow_database_directory] [get_db flow_report_name]]

  if {![file exists $out_dir]} {
    file mkdir $out_dir
  }

  #- write design and library information
  write_netlist -top_module_first -top_module $design [file join $out_dir $design.v]
  write_mmmc > [file join $out_dir mmmc_config.tcl]

  # [stevo]: defined in innovus_config.tcl
  write_lvs_netlist

  #- write extraction information
  write_extraction_spec -out_dir $out_dir
  file rename -force qrc.cmd [file join $out_dir qrc.cmd]

  #- write init_design sequence for STA flow
  set FH [open $out_dir/init_sta.tcl w]
  puts $FH "read_mmmc [file join $out_dir mmmc_config.tcl]"
  puts $FH "read_netlist [file join $out_dir $design.v]"
  puts $FH "init_design"
  close $FH
}

##############################################################################
# STEP schedule_sta
##############################################################################
create_flow_step -name schedule_sta -skip_db -owner cadence {
  if {[get_db flow_branch] ne ""} {
    set branch_name [get_db flow_branch]_[get_db flow_report_name]
  } else {
    set branch_name [get_db flow_report_name]
  }

  #FlowtoolPredictHint ArgumentRandomise -branch
  schedule_flow \
    -flow sta \
    -branch $branch_name \
    -db [file join [get_db flow_database_directory] [get_db flow_report_name] init_sta.tcl] \
    -include_in_metrics \
    -no_sync
}

