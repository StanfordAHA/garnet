# Flowkit v0.2

# Copyright (C) 2014 Cadence Design Systems, Inc.
# All Rights Reserved.
# CCRNI-0013
#
# This work is protected by copyright laws and contains Cadence proprietary
# and confidential information.  No part of this file may be reproduced,
# modified, re-published, used, disclosed or distributed in any way, in any
# medium, whether in whole or in part, without prior written permission from
# Cadence Design Systems, Inc.
#
#===========================================================================
#- run_flow.tcl: source this file to define required flow objects and consume
#                all customizations

################################################################################
# Flow Setup
################################################################################
# Template change number: 1331611

#- Setup flow script path
if { ![is_attribute -obj_type root flow_source_directory] } {
  define_attribute flow_source_directory \
    -category flow \
    -data_type string \
    -default_value [file normalize [file dirname [info script]]] \
    -help_string "Flow script source location" \
    -obj_type root
}

#- Setup canonical flow path
if { ![is_attribute -obj_type root flow_report_name]} {
  define_attribute flow_report_name \
    -category flow \
    -data_type string \
    -default_value "" \
    -help_string "Name to use during report generation" \
    -obj_type root
}

################################################################################
# Define Flow Features
################################################################################

#+--------------------------+-------------------------------------------------------------------+----------+
#| Feature                  | Description                                                       | Status   |
#+--------------------------+-------------------------------------------------------------------+----------+
#| clock_design             | Run discrete clock expansion                                      | disabled |
#--- the following features are mutually exclusive (dft_style group)
#| dft_compressor           | Add flow support for scan chains with compression insertion       | disabled |
#| dft_simple               | Add flow support for scan chain insertion                         | disabled |
#---
#| express                  | Enable express synthesis and implementation flow                  | disabled |
#| opt_early_cts            | Implement early clock tree for use during prects optimization     | disabled |
#| opt_eco                  | Run opt_design during eco flow                                    | disabled |
#| opt_postcts_hold_disable | Disable postcts hold fixing                                       | disabled |
#| opt_postcts_split        | Run postcts opt_design for setup and hold as separate steps       | disabled |
#| opt_postroute_split      | Run postroute opt_design for setup and hold as separate steps     | disabled |
#| opt_signoff_area         | Run signoff base area optimization as part implementation flow    | disabled |
#| opt_signoff_drv          | Run signoff base drv optimization as part implementation flow     | disabled |
#| opt_signoff_dynamic      | Run signoff base dynamic optimization as part implementation flow | disabled |
#| opt_signoff_hold         | Run signoff base hold optimization as part implementation flow    | disabled |
#| opt_signoff_leakage      | Run signoff base leakage optimization as part implementation flow | disabled |
#| opt_signoff_setup        | Run signoff base setup optimization as part implementation flow   | disabled |
#| report_clp               | Add CLP dofile generation and checks to the flow                  | disabled |
#| report_inline            | Run report generation as part of parent flow versus schedule_flow | disabled |
#| report_lec               | Add LEC dofile generation and checks to the flow                  | enabled  |
#| route_secondary_nets     | Route secondary PG nets before route_design                       | disabled |
#| route_track_opt          | Adds track based optimization to route_design                     | disabled |
#| sta_dmmc                 | Use DMMMC achitecure for running STA runs                         | disabled |
#| sta_eco                  | Generate ECO data for Tempus TSO flow                             | disabled |
#| sta_glitch               | Add glitch analysis reports to STA flow                           | disabled |
#--- the following features are mutually exclusive (synth_style group)
#| synth_physical           | Full physically aware synthesis flow                              | disabled |
#| synth_spatial            | Physically aware synthesis flow with spatial final optimization   | disabled |
#---
#+--------------------------+-------------------------------------------------------------------+----------+

set_db flow_template_type {block}
set_db flow_template_version {1}
set_db flow_template_feature_definition {express disabled report_inline disabled report_lec enabled report_clp disabled dft_simple disabled dft_compressor disabled synth_spatial disabled synth_physical disabled opt_early_cts disabled clock_design disabled opt_postcts_hold_disable disabled opt_postcts_split disabled route_track_opt disabled route_secondary_nets disabled opt_postroute_split disabled opt_signoff_area disabled opt_signoff_drv disabled opt_signoff_setup disabled opt_signoff_hold disabled opt_signoff_leakage disabled opt_signoff_dynamic disabled opt_eco disabled sta_dmmc disabled sta_eco disabled sta_glitch disabled}

################################################################################
# Load Flow Files
################################################################################

source [file join [file dirname [info script]] flow common_steps.tcl]
source [file join [file dirname [info script]] flow genus_steps.tcl]
source [file join [file dirname [info script]] flow innovus_steps.tcl]
source [file join [file dirname [info script]] flow tempus_steps.tcl]
source [file join [file dirname [info script]] design_config.tcl]

##############################################################################
# Define Implementation Subflows
##############################################################################

create_flow -name syn_generic -owner cadence -tool genus -tool_options -disable_user_startup {block_start init_design set_dont_touch create_cost_group run_syn_gen block_finish schedule_report_generic}

create_flow -name syn_map -owner cadence -tool genus -tool_options -disable_user_startup {block_start set_dont_use run_syn_map block_finish schedule_report_map}

create_flow -name syn_opt -owner cadence -tool genus -tool_options -disable_user_startup {block_start set_dont_use run_syn_opt block_finish schedule_report_synth genus_to_innovus}

create_flow -name fplan -owner cadence -tool innovus -tool_options -disable_user_startup {block_start init_floorplan add_tracks block_finish schedule_report_fplan}

create_flow -name prects -owner cadence -tool innovus -tool_options -disable_user_startup {block_start set_dont_use run_place_opt stream_out block_finish schedule_report_prects}

create_flow -name cts -owner cadence -tool innovus -tool_options -disable_user_startup {block_start set_dont_use add_clock_spec add_clock_tree fix_pulse_width add_tieoffs block_finish schedule_report_postcts}

create_flow -name postcts -owner cadence -tool innovus -tool_options -disable_user_startup {block_start run_opt_postcts_hold block_finish schedule_report_postcts}

create_flow -name route -owner cadence -tool innovus -tool_options -disable_user_startup {block_start set_dont_use add_fillers run_route block_finish schedule_report_postroute}

create_flow -name postroute -owner cadence -tool innovus -tool_options -disable_user_startup {block_start set_dont_use run_opt_postroute power_vias stream_out block_finish innovus_to_tempus report_postroute schedule_sta}

create_flow -name eco -owner cadence -tool innovus -tool_options -disable_user_startup {eco_start init_eco place_eco route_eco schedule_report_postroute}

##############################################################################
# Define Reporting Subflows
##############################################################################

create_flow -name report_synth -owner cadence -tool genus -tool_options -disable_user_startup {report_start report_area_genus report_timing_summary_late_genus report_late_paths report_power_genus report_finish}

create_flow -name fv_genus -owner cadence -tool genus {flow_step:genus_to_lec}

create_flow -name lec -owner cadence -tool lec

create_flow -name report_fplan -owner cadence -tool innovus -tool_options -disable_user_startup {report_start report_area_innovus report_route_drc report_finish}

create_flow -name report_prects -owner cadence -tool innovus -tool_options -disable_user_startup {report_start report_area_innovus report_timing_late_innovus report_late_paths report_power_innovus report_finish}

create_flow -name report_postcts -owner cadence -tool innovus -tool_options -disable_user_startup {report_start report_area_innovus report_timing_early_innovus report_early_paths report_timing_late_innovus report_late_paths report_clock_timing report_power_innovus report_finish}

create_flow -name report_postroute -owner cadence -tool innovus -tool_options -disable_user_startup {report_start report_area_innovus report_timing_early_innovus report_early_paths report_timing_late_innovus report_late_paths report_clock_timing report_power_innovus report_route_drc report_route_density report_finish}

create_flow -name sta -owner cadence -tool tempus -tool_options -disable_user_startup {signoff_start read_parasitics update_timing check_timing report_timing_late report_late_paths report_timing_early report_early_paths signoff_finish}

################################################################################
# Define Block Flow
################################################################################
create_flow -name block -owner cadence {syn_generic syn_map syn_opt fplan prects cts route postroute}

set_db flow_current flow:block

################################################################################
# Load Flow & Tool Customizations
################################################################################

source [file join [file dirname [info script]] flow_config.tcl]

#- Apply tool settings needed before a DB is loaded
if {[get_db program_short_name] ne {}} {

  if [file exists [file join [get_db flow_source_directory] [get_db program_short_name]_config.tcl]] {
    #- Validate PLACEHOLDER content in config files
    set FH [open [file join [get_db flow_source_directory] [get_db program_short_name]_config.tcl]]
    set lines [read $FH]
    close $FH
    foreach line [split $lines "\n"] {
      if {[regexp {^\s*\#} $line]} {continue}
      if {[regexp {PLACEHOLDER} $line]} {
        error "Found PLACEHOLDER content in [file join [get_db flow_source_directory] [get_db program_short_name]_config.tcl]\n\t$line"
      }
    }

    source [file join [get_db flow_source_directory] [get_db program_short_name]_config.tcl]
  } else {
    error "Tool config [file join [get_db flow_source_directory] [get_db program_short_name]_config.tcl] file not found."
  }
}

