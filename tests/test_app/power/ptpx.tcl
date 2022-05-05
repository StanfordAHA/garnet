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
# Author : Kalhan Koul
# Date   : Mar 30, 2022
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

set_app_var search_path      ". $ptpx_additional_search_path $search_path ../netlist/"
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
read_verilog "../netlist/global_controller.vcs.v"
read_verilog "../netlist/glb_top.vcs.v"
read_verilog "../netlist/glb_tile.vcs.v"
read_verilog "../netlist/tile_array.vcs.v"
read_verilog "../netlist/Tile_MemCore.vcs.v"
read_verilog "../netlist/Tile_PE.vcs.v"
#read_verilog "../netlist/sram.v"
#read_verilog "../netlist/tile_array.sram.v"

current_design "GarnetSOC_pad_frame"

link_design

if { $::env(chkpt) == "True" } {
  save_session chk_post_link
}

# Read in the SDC and parasitics
read_sdc -echo $ptpx_sdc 
source loop_break_Interconnect.tcl

read_parasitics -format spef ./../netlist/global_controller.spef.gz -path [all_instances -hierarchy global_controller]
read_parasitics -format spef ./../netlist/glb_top.spef.gz -path [all_instances -hierarchy global_buffer]
read_parasitics -format spef ./../netlist/glb_tile.spef.gz -path [all_instances -hierarchy glb_tile]
read_parasitics -format spef ./../netlist/tile_array.spef.gz -path [all_instances -hierarchy Interconnect]
read_parasitics -format spef ./../netlist/Tile_PE.spef.gz -path [all_instances -hierarchy Tile_PE]
read_parasitics -format spef ./../netlist/Tile_MemCore.spef.gz -path [all_instances -hierarchy Tile_MemCore]
read_parasitics -format spef $ptpx_spef


if { $::env(chkpt) == "True" } {
  save_session chk_post_link
}

if { $::env(reports) == "True" } {
  report_annotated_parasitics -check > reports/${ptpx_design_name}.parasitics.rpt
  check_constraints -verbose > reports/${ptpx_design_name}.checkconstraints.rpt
  report_activity_file_check $ptpx_saif -strip_path $ptpx_strip_path > reports/${ptpx_design_name}.activity.pre.rpt
}

# Read in switching activity
read_fsdb "./../novas.fsdb" -strip_path "top/dut" -path "core/u_aha_garnet/u_garnet"
#read_saif "./../run.saif" -strip_path "top/dut" -path "core/u_aha_garnet/u_garnet" -quiet

if { $::env(chkpt) == "True" } {
  save_session chk_post_saif
}

#-------------------------------------------------------------------------
# Power analysis
# Note: If fails on segfault, increase stack size with 'ulimit -s unlimited' in terminal
#-------------------------------------------------------------------------

update_timing -full

if { $::env(reports) == "True" } {
  check_power > reports/${ptpx_design_name}.checkpower.rpt
}

update_power

#-------------------------------------------------------------------------
# Final reports
#-------------------------------------------------------------------------

if { $::env(reports) == "True" } {
  report_switching_activity > reports/${ptpx_design_name}.activity.post.rpt
}

report_power -nosplit -hierarchy -levels 6 -sort_by total_power > reports/${ptpx_design_name}.power.rpt

if { $::env(reports) == "True" } {
  report_power -nosplit -hierarchy > reports/${ptpx_design_name}.power.hier.rpt
  report_power -nosplit -hierarchy -leaf -levels 10 > reports/${ptpx_design_name}.power.cell.rpt
}


exit
