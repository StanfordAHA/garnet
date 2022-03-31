#=========================================================================
# ptpx.tcl
#=========================================================================
# Use Synopsys PrimeTime to run power analysis
#
# - Gate-level power analysis
# - Averaged power analysis
# - save_session is your friend
#
# Requires:
#
# - *.v    -- gate-level netlist
# - *.saif -- switching activity dump from gate-level simulation
# - *.sdc  -- constraints (e.g., create_clock) from PnR
# - *.spef -- parasitics from PnR
#
# Author : Christopher Torng
# Date   : May 20, 2019
#

#-------------------------------------------------------------------------
# Designer interface
#-------------------------------------------------------------------------
# Source the designer interface script, which sets up ASIC design kit
# variables and inputs.

source -echo -verbose designer-interface.tcl

#-------------------------------------------------------------------------
# Setup
#-------------------------------------------------------------------------

# Set up paths and libraries

set_app_var search_path      ". $ptpx_additional_search_path $search_path ./inputs/"
set_app_var target_library   $ptpx_target_libraries
set_app_var link_library     [join "
                               *
                               $ptpx_target_libraries
                               $ptpx_extra_link_libraries
                             "]

# Set up power analysis

set_app_var power_enable_analysis true
set_app_var power_analysis_mode time_based

set_app_var report_default_significant_digits 3

###
if { $::env(chkpt) == "True" } {
  save_session chk_env
} 
#-------------------------------------------------------------------------
# Read design
#-------------------------------------------------------------------------

# Read and link the design

read_verilog   $ptpx_gl_netlist

current_design $ptpx_design_name

link_design

###
if { $::env(chkpt) == "True" } {
  save_session chk_post_link
}

# Read in switching activity

# report_activity_file_check $ptpx_saif -strip_path $ptpx_strip_path \
#   > reports/${ptpx_design_name}.activity.pre.rpt

read_fsdb $ptpx_fsdb -strip_path $ptpx_strip_path

###
if { $::env(chkpt) == "True" } {
  save_session chk_post_saif
}

# Read in the SDC and parasitics

read_sdc -echo $ptpx_sdc

check_constraints -verbose \
  > reports/${ptpx_design_name}.checkconstraints.rpt

if { $::env(chkpt) == "True" } {
  save_session chk_post_constraints
}

read_parasitics -format spef ./inputs/glb_tile.spef.gz -path [all_instances -hierarchy glb_tile]
read_parasitics -format spef $ptpx_spef

report_annotated_parasitics -check \
  > reports/${ptpx_design_name}.parasitics.rpt

#-------------------------------------------------------------------------
# Power analysis
#-------------------------------------------------------------------------

###
if { $::env(chkpt) == "True" } {
  save_session chk_pre_timing
}

update_timing -full

check_power \
  > reports/${ptpx_design_name}.checkpower.rpt

update_power

#-------------------------------------------------------------------------
# Final reports
#-------------------------------------------------------------------------

report_switching_activity \
  > reports/${ptpx_design_name}.activity.post.rpt

report_power -nosplit \
  > reports/${ptpx_design_name}.power.rpt

report_power -nosplit -hierarchy -leaf -levels 10 -sort_by total_power \
  > reports/${ptpx_design_name}.power.hier.rpt

report_power -nosplit -hierarchy -leaf -levels 10 -sort_by total_power -groups clock_network \
  > reports/${ptpx_design_name}.power.hier.cn.rpt

report_power -nosplit -cell -leaf -sort_by total_power \
  > reports/${ptpx_design_name}.power.cell.rpt

report_power -nosplit -cell -leaf -sort_by total_power -groups clock_network \
  > reports/${ptpx_design_name}.power.cell.cn.rpt

# Report power summary and breakdown of sub-instances
foreach instance [split $::env(instances) ,] {
    current_instance "/${ptpx_design_name}/${instance}"

    report_power -nosplit \
      > reports/${instance}.power.rpt
    
    report_power -nosplit -hierarchy -leaf -levels 10 -sort_by total_power \
      > reports/${instance}.power.hier.rpt

    report_power -nosplit -cell -leaf -sort_by total_power \
      > reports/${instance}.power.cell.rpt

    report_power -nosplit -cell -leaf -sort_by total_power -groups clock_network\
      > reports/${instance}.power.cell.cn.rpt

    report_power -nosplit -hierarchy -leaf -levels 10 -sort_by total_power -groups clock_network \
      > reports/${instance}.power.hier.cn.rpt
}

###
save_session chk_final

exit

