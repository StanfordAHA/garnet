# Flowkit v0.2
#- innovus_steps.tcl : defines Innovus based flowsteps


#=============================================================================
# Flow: fplan
#=============================================================================

##############################################################################
# STEP add_tracks
##############################################################################
create_flow_step -name add_tracks -skip_db -owner cadence {
  #- generate tracks after creating floorplan
  add_tracks
}


#===========================================================================
# Flow: prects
#===========================================================================

##############################################################################
# STEP run_place_opt
##############################################################################
create_flow_step -name run_place_opt -skip_db -owner cadence {
  #- perform global placement and ideal clock setup optimization
  place_opt_design -report_dir debug -report_prefix [get_db flow_report_name]
}


#=============================================================================
# Flow: cts
#=============================================================================

##############################################################################
# STEP add_clock_spec
##############################################################################
create_flow_step -name add_clock_spec -skip_db -owner cadence {
  #- automatically create clock spec if one is not available
  if {[llength [get_clock_tree_sinks  *]] == 0} {
    create_clock_tree_spec
  } else {
    puts "INFO: reusing existing clock tree spec"
    puts "        to reload a new one use 'delete_clock_tree_spec' and 'read_ccopt_config"
  }
}

##############################################################################
# STEP add_clock_tree
##############################################################################
create_flow_step -name add_clock_tree -skip_db -owner cadence {
  #- implement clock trees and propagated clock setup optimization
  ccopt_design -hold -report_dir debug -report_prefix [get_db flow_report_name]
}

##############################################################################
# STEP add_tieoffs
##############################################################################
create_flow_step -name add_tieoffs -skip_db -owner cadence {
  #- insert dedicated tieoff models
  if {[get_db add_tieoffs_cells] ne "" } {
    delete_tieoffs
    add_tieoffs -matching_power_domains true
  }
}

#=============================================================================
# Flow: postcts
#=============================================================================

##############################################################################
# STEP run_opt_postcts_hold
##############################################################################
create_flow_step -name run_opt_postcts_hold -skip_db -owner cadence {
  #- perform postcts hold optimization
  opt_design -post_cts -hold -report_dir debug -report_prefix [get_db flow_report_name]
}


#=============================================================================
# Flow: route
#=============================================================================

##############################################################################
# STEP add_fillers
##############################################################################
create_flow_step -name add_fillers -skip_db -owner cadence {
  #- insert filler cells before final routing
  if {[get_db add_fillers_cells] ne "" } {
    add_fillers
  }
}

##############################################################################
# STEP run_route
##############################################################################
create_flow_step -name run_route -skip_db -owner cadence {
  #- perform detail routing and DRC cleanup
  route_design
}


#=============================================================================
# Flow: postroute
#=============================================================================

##############################################################################
# STEP run_opt_postroute
##############################################################################
create_flow_step -name run_opt_postroute -skip_db -owner cadence {
  #- perform postroute and SI based setup optimization
  opt_design -post_route -setup -hold -report_dir debug -report_prefix [get_db flow_report_name]
}


#=============================================================================
# Flow: eco
#=============================================================================

##############################################################################
# STEP eco_start
##############################################################################
create_flow_step -name eco_start -skip_db -owner cadence {
}

##############################################################################
# STEP place_eco
##############################################################################
create_flow_step -name place_eco -skip_db -owner cadence {
  place_eco
}

##############################################################################
# STEP route_eco
##############################################################################
create_flow_step -name route_eco -skip_db -owner cadence {
  route_eco
}

##############################################################################
# STEP eco_finish
##############################################################################
create_flow_step -name eco_finish -owner cadence {
}


#===========================================================================
# Flow: report_innovus
#===========================================================================

##############################################################################
# STEP schedule_report_fplan
##############################################################################
create_flow_step -name schedule_report_fplan -skip_db -exclude_time_metric -owner cadence {
  if {[get_db flow_branch] ne ""} {
    set branch_name [get_db flow_branch]_[get_db flow_report_name]
  } else {
    set branch_name [get_db flow_report_name]
  }

  schedule_flow \
    -flow report_fplan  \
    -branch $branch_name \
    -no_sync \
    -include_in_metrics
}

##############################################################################
# STEP schedule_report_prects
##############################################################################
create_flow_step -name schedule_report_prects -skip_db -exclude_time_metric -owner cadence {
  if {[get_db flow_branch] ne ""} {
    set branch_name [get_db flow_branch]_[get_db flow_report_name]
  } else {
    set branch_name [get_db flow_report_name]
  }

  schedule_flow \
    -flow report_prects  \
    -branch $branch_name \
    -no_sync \
    -include_in_metrics
}

##############################################################################
# STEP schedule_report_postcts
##############################################################################
create_flow_step -name schedule_report_postcts -skip_db -exclude_time_metric -owner cadence {
  if {[get_db flow_branch] ne ""} {
    set branch_name [get_db flow_branch]_[get_db flow_report_name]
  } else {
    set branch_name [get_db flow_report_name]
  }

  schedule_flow \
    -flow report_postcts  \
    -branch $branch_name \
    -no_sync \
    -include_in_metrics
}

##############################################################################
# STEP schedule_report_postroute
##############################################################################
create_flow_step -name schedule_report_postroute -skip_db -exclude_time_metric -owner cadence {
  if {[get_db flow_branch] ne ""} {
    set branch_name [get_db flow_branch]_[get_db flow_report_name]
  } else {
    set branch_name [get_db flow_report_name]
  }

  schedule_flow \
    -flow report_postroute  \
    -branch $branch_name \
    -no_sync \
    -include_in_metrics
}

##############################################################################
# STEP report_area_innovus
##############################################################################
create_flow_step -name report_area_innovus -skip_db -exclude_time_metric -owner cadence {
  report_summary -no_html -out_dir debug -out_file [get_db flow_report_directory]/[get_db flow_report_name]/qor.rpt
  report_area -out_file [get_db flow_report_directory]/[get_db flow_report_name]/area.summary.rpt -min_count 1000
}

##############################################################################
# STEP report_timing_late_innovus
##############################################################################
create_flow_step -name report_timing_late_innovus -skip_db -exclude_time_metric -owner cadence {
  #- Update the timer for setup and write reports
  time_design -expanded_views -report_only -report_dir debug -report_prefix [get_db flow_report_name]

  #- Reports that describe timing health
  report_constraint -all_violators                      > [get_db flow_report_directory]/[get_db flow_report_name]/setup.all_violators.rpt
  report_analysis_summary -merged_groups                > [get_db flow_report_directory]/[get_db flow_report_name]/setup.analysis_summary.rpt
}

##############################################################################
# STEP report_timing_early_innovus
##############################################################################
create_flow_step -name report_timing_early_innovus -skip_db -exclude_time_metric -owner cadence {
  #- Update the timer for hold and write reports
  time_design -expanded_views -hold -report_only -report_dir debug -report_prefix [get_db flow_report_name]

  #- Reports that describe timing health
  report_constraint -all_violators -early               > [get_db flow_report_directory]/[get_db flow_report_name]/hold.all_violators.rpt
  report_analysis_summary -early -merged_groups         > [get_db flow_report_directory]/[get_db flow_report_name]/hold.analysis_summary.rpt
}

##############################################################################
# STEP report_clock_timing
##############################################################################
create_flow_step -name report_clock_timing -skip_db -exclude_time_metric -owner cadence {
  #- Reports that check clock implementation
  report_clock_timing -type summary > [get_db flow_report_directory]/[get_db flow_report_name]/clock.summary.rpt
  report_clock_timing -type latency > [get_db flow_report_directory]/[get_db flow_report_name]/clock.latency.rpt
  report_clock_timing -type skew    > [get_db flow_report_directory]/[get_db flow_report_name]/clock.skew.rpt
}

##############################################################################
# STEP report_power_innovus
##############################################################################
create_flow_step -name report_power_innovus -skip_db -exclude_time_metric -owner cadence {
  #- Ensure leakge power view is active when specified
  if {([get_db power_leakage_power_view] != "") && \
      ([lsearch -exact [get_db [concat [get_db analysis_views -if {.is_setup}] [get_db analysis_views -if {.is_hold}]] .name] [get_db power_leakage_power_view]] == -1)} {
    set_analysis_view \
      -setup [lsort -unique [concat [get_db power_leakage_power_view] [get_db [get_db analysis_views -if {.is_setup}] .name]]] \
      -hold [get_db [get_db analysis_views -if {.is_hold}] .name]
  }

  report_power -no_wrap -out_file [get_db flow_report_directory]/[get_db flow_report_name]/power.all.rpt
}

##############################################################################
# STEP report_route_process
##############################################################################
create_flow_step -name report_route_process -skip_db -exclude_time_metric -owner cadence {
  #- Reports that process rules
  check_process_antenna -out_file [get_db flow_report_directory]/[get_db flow_report_name]/route.antenna.rpt
  check_filler -out_file [get_db flow_report_directory]/[get_db flow_report_name]/route.filler.rpt
}

##############################################################################
# STEP report_route_drc
##############################################################################
create_flow_step -name report_route_drc -skip_db -exclude_time_metric -owner cadence {
  #- Reports that check signal routing
  check_drc -out_file [get_db flow_report_directory]/[get_db flow_report_name]/route.drc.report
  check_connectivity -out_file [get_db flow_report_directory]/[get_db flow_report_name]/route.open.report
}

##############################################################################
# STEP report_route_density
##############################################################################
create_flow_step -name report_route_density -skip_db -exclude_time_metric -owner cadence {
  check_metal_density -report [get_db flow_report_directory]/[get_db flow_report_name]/route.metal_density.rpt
  check_cut_density -out_file [get_db flow_report_directory]/[get_db flow_report_name]/route.cut_density.rpt
}

