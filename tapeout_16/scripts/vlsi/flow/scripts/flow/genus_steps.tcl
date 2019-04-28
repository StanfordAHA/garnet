# Flowkit v0.2
#- genus_steps.tcl : defines Genus based flowsteps


#===========================================================================
# Flow: synth
#===========================================================================

##############################################################################
# STEP create_cost_group
##############################################################################
create_flow_step -name create_cost_group -skip_db -owner cadence {
  #- Clear existinng path_groups
  if {[llength [get_db -u cost_groups -if {.name != default }]] > 0} {
    delete_object [get_db cost_groups -if {.name != default}]
  }

  #- Add basic path_groups
  foreach view [get_db analysis_views -if {.is_setup}] {
    set_constraint_mode [get_db $view .name]
    group_path -name in2out -from [all_inputs] -to [all_outputs]
    if {[sizeof_collection [all_registers]] > 0} {
      group_path -name in2reg -from [all_inputs] -to [all_registers]
      group_path -name reg2out -from [all_registers] -to [all_outputs]
      group_path -name reg2reg -from [all_registers] -to [all_registers]
    }
  }
}

##############################################################################
# STEP run_syn_gen
##############################################################################
create_flow_step -name run_syn_gen -owner cadence {
  #- Load genus_config.tcl to support stage dependent settings
  set_db flow_report_name syn_generic
  uplevel #0 source [file join [get_db flow_source_directory] genus_config.tcl]

  #- Synthesize to generic gates
  syn_generic
}

##############################################################################
# STEP run_syn_map
##############################################################################
create_flow_step -name run_syn_map -owner cadence {
  #- Load genus_config.tcl to support stage dependent settings
  set_db flow_report_name syn_map
  uplevel #0 source [file join [get_db flow_source_directory] genus_config.tcl]

  #- Synthesize to target library gates
  syn_map

}

##############################################################################
# STEP run_syn_opt
##############################################################################
create_flow_step -name run_syn_opt -owner cadence {
  #- Load genus_config.tcl to support stage dependent settings
  set_db flow_report_name syn_opt
  uplevel #0 source [file join [get_db flow_source_directory] genus_config.tcl]

  #- Synthesize to optimized gates
  syn_opt
}

##############################################################################
# STEP genus_to_innovus
##############################################################################
create_flow_step -name genus_to_innovus -skip_db -owner cadence {
  #- Apply change_name rules
  update_names \
    [current_design] \
    -force \
    -verilog \
    -module \
    -append_log \
    -log [file join [get_db flow_report_directory] [get_db flow_report_name] change_names.log]

  #- prevent SDCs from having set_timing_derate and group_path since these are ignored by innovus
  set_db write_sdc_exclude {set_timing_derate group_path}

  #- write output files
  write_design \
    -innovus \
    -gzip_files \
    -basename [file normalize [file join [get_db flow_database_directory] [get_db flow_report_name] [get_db [current_design] .name]]]

  set_db flow_post_db_overwrite [file join [get_db flow_database_directory] [get_db flow_report_name] [get_db [current_design] .name].invs_setup.tcl]
}


#===========================================================================
# Flow: report_genus
#===========================================================================

##############################################################################
# STEP schedule_report_generic
##############################################################################
create_flow_step -name schedule_report_generic -skip_db -exclude_time_metric -owner cadence {
  if {[get_db flow_branch] ne ""} {
    set branch_name [get_db flow_branch]_[get_db flow_report_name]
  } else {
    set branch_name [get_db flow_report_name]
  }

  schedule_flow \
    -flow report_synth  \
    -branch $branch_name \
    -no_sync \
    -include_in_metrics
}

##############################################################################
# STEP schedule_report_map
##############################################################################
create_flow_step -name schedule_report_map -skip_db -exclude_time_metric -owner cadence {
  if {[get_db flow_branch] ne ""} {
    set branch_name [get_db flow_branch]_[get_db flow_report_name]
  } else {
    set branch_name [get_db flow_report_name]
  }

  schedule_flow \
    -flow report_synth  \
    -branch $branch_name \
    -no_sync \
    -include_in_metrics
}

##############################################################################
# STEP schedule_report_synth
##############################################################################
create_flow_step -name schedule_report_synth -skip_db -exclude_time_metric -owner cadence {
  if {[get_db flow_branch] ne ""} {
    set branch_name [get_db flow_branch]_[get_db flow_report_name]
  } else {
    set branch_name [get_db flow_report_name]
  }

  schedule_flow \
    -flow report_synth  \
    -branch $branch_name \
    -no_sync \
    -include_in_metrics
}

##############################################################################
# STEP report_area_genus
##############################################################################
create_flow_step -name report_area_genus -skip_db -exclude_time_metric -owner cadence {
  report_area -min_count 5000 > [get_db flow_report_directory]/[get_db flow_report_name]/area.rpt
  report_dp                   > [get_db flow_report_directory]/[get_db flow_report_name]/datapath.rpt
}

##############################################################################
# STEP report_timing_summary_late_genus
##############################################################################
create_flow_step -name report_timing_summary_late_genus -skip_db -exclude_time_metric -owner cadence {
  report_qor > [get_db flow_report_directory]/[get_db flow_report_name]/qor.rpt
}

##############################################################################
# STEP report_power_genus
##############################################################################
create_flow_step -name report_power_genus -skip_db -exclude_time_metric -owner cadence {
  report_gates -power   > [get_db flow_report_directory]/[get_db flow_report_name]/gates_power.rpt
  report_clock_gating   > [get_db flow_report_directory]/[get_db flow_report_name]/clockgating.rpt
  report_power -depth 0 > [get_db flow_report_directory]/[get_db flow_report_name]/power.rpt
}

