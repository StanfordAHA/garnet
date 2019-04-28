# Flowkit v0.2
################################################################################
# Tool attributes (design & library not required)
#
#  Attributes used to drive tool behavior.  Most typically these are root level
#  attributes.  All root attributes can be listed by using 'report_obj -all' or
#  by category using 'report_obj -all -verbose'
#
#  Further attribute help can be obtained by using the command 'help <ATTRIBUTE>'
#
################################################################################

if {[get_db flow_step_current] ne ""} {
  puts "INFO: (FLOW-102) : Loading [file tail [info script]] with [get_db flow_step_current]"
} else {
  puts "INFO: (FLOW-102) : Loading [file tail [info script]]"
}

################################################################################
# ATTRIBUTES APPLIED BEFORE LOADING A LIBRARY OR DATABASE
################################################################################

# General attributes  [get_db -category init]
#-------------------------------------------------------------------------------
if {[info exists ::env(LSB_MAX_NUM_PROCESSORS)]} {
  set_multi_cpu_usage -local_cpu  $::env(LSB_MAX_NUM_PROCESSORS)
}

set_multi_cpu_usage -local_cpu  16
################################################################################
# ATTRIBUTES APPLIED AFTER LOADING A LIBRARY OR DATABASE
################################################################################
if {[get_db current_design] eq ""} {return}

# Design attributes  [get_db -category design]
#-------------------------------------------------------------------------------
set_db design_process_node                        16

# Timing attributes  [get_db -category timing]
#-------------------------------------------------------------------------------
set_db timing_analysis_cppr                       both
set_db timing_analysis_type                       ocv
set_db timing_enable_simultaneous_setup_hold_mode true

# Delaycal attributes  [get_db -category delaycal]
#-------------------------------------------------------------------------------
set_db delaycal_enable_si                         true

