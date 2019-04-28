# Flowkit v0.2
#- tempus_steps.tcl : defines Tempus based flowsteps


#=============================================================================
# Flow: sta
#=============================================================================

##############################################################################
# STEP update_timing
##############################################################################
create_flow_step -name update_timing -skip_db -owner cadence {
  #- update timer for signoff timing reports
  update_timing -full
}

##############################################################################
# STEP check_timing
##############################################################################
create_flow_step -name check_timing -skip_db -exclude_time_metric -owner cadence {
  #- Reports that check design health
  check_design -all -no_html -out_file  [get_db flow_report_directory]/[get_db flow_report_name]/check_design.rpt
  report_annotated_parasitics         > [get_db flow_report_directory]/[get_db flow_report_name]/annotated.rpt
  report_analysis_coverage            > [get_db flow_report_directory]/[get_db flow_report_name]/coverage.rpt

  #- Reports that describe constraints
  report_clocks                       > [get_db flow_report_directory]/[get_db flow_report_name]/clocks.rpt
  report_case_analysis                > [get_db flow_report_directory]/[get_db flow_report_name]/case_analysis.rpt
  report_inactive_arcs                > [get_db flow_report_directory]/[get_db flow_report_name]/inactive_arcs.rpt
}

##############################################################################
# STEP report_timing_late
##############################################################################
create_flow_step -name report_timing_late -skip_db -exclude_time_metric -owner cadence {
  #- Reports that describe timing health
  report_analysis_summary -late -merged_groups  > [get_db flow_report_directory]/[get_db flow_report_name]/setup.analysis_summary.rpt
  report_constraint -all_violators              > [get_db flow_report_directory]/[get_db flow_report_name]/setup.all_violators.rpt
}

##############################################################################
# STEP report_timing_early
##############################################################################
create_flow_step -name report_timing_early -skip_db -exclude_time_metric -owner cadence {
  #- Reports that describe early timing health
  report_analysis_summary -early -merged_groups > [get_db flow_report_directory]/[get_db flow_report_name]/hold.analysis_summary.rpt
  report_constraint       -early -all_violators > [get_db flow_report_directory]/[get_db flow_report_name]/hold.all_violators.rpt
}


