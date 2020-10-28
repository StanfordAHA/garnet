#=========================================================================
# ptpx.tcl
#=========================================================================
# Use Synopsys PrimeTime to run power analysis
#
# - Gate-level power analysis
# - Averaged power analysis
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

set batch_path_str ""
# Check for batch_mode
if { $::env(batch) == "True" } {
  set tile_name  $::env(tile_name)
  set tile_alias $::env(tile_alias)
  set batch_path_str "_${tile_alias}_${tile_name}"
} 

#-------------------------------------------------------------------------
# Setup
#-------------------------------------------------------------------------

# Set up paths and libraries

set_app_var search_path      ". $ptpx_additional_search_path $search_path"
set_app_var target_library   $ptpx_target_libraries
set_app_var link_library     [join "
                               *
                               $ptpx_target_libraries
                               $ptpx_extra_link_libraries
                             "]

# Set up power analysis

set_app_var power_enable_analysis true
set_app_var power_analysis_mode   averaged

set_app_var report_default_significant_digits 3

#-------------------------------------------------------------------------
# Read design
#-------------------------------------------------------------------------

# Read and link the design

read_verilog   $ptpx_gl_netlist
current_design $ptpx_design_name

link_design

# Read in switching activity

report_activity_file_check $ptpx_saif -strip_path $ptpx_strip_path \
  > reports/${ptpx_design_name}${batch_path_str}.activity.pre.rpt

read_saif $ptpx_saif -strip_path $ptpx_strip_path -quiet

# Read in the SDC and parasitics

read_sdc -echo $ptpx_sdc

check_constraints -verbose \
  > reports/${ptpx_design_name}${batch_path_str}.checkconstraints.rpt

read_parasitics -format spef $ptpx_spef

report_annotated_parasitics -check \
  > reports/${ptpx_design_name}${batch_path_str}.parasitics.rpt

#-------------------------------------------------------------------------
# Power analysis
#-------------------------------------------------------------------------

update_timing -full

check_power \
  > reports/${ptpx_design_name}${batch_path_str}.checkpower.rpt

update_power

#-------------------------------------------------------------------------
# Final reports
#-------------------------------------------------------------------------

report_switching_activity \
  > reports/${ptpx_design_name}${batch_path_str}.activity.post.rpt

report_power -nosplit \
  > reports/${ptpx_design_name}${batch_path_str}.power.rpt

report_power -nosplit -hierarchy \
  > reports/${ptpx_design_name}${batch_path_str}.power.hier.rpt

report_power -nosplit -hierarchy -leaf -levels 10 \
  > reports/${ptpx_design_name}${batch_path_str}.power.cell.rpt

exit

