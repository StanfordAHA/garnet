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

# General attributes
#-------------------------------------------------------------------------------

set_db max_cpus_per_server  8

# Optimization attributes  [get_db -category netlist]
#-------------------------------------------------------------------------------
#set_db syn_generic_effort    medium
#set_db syn_map_effort        << PLACEHOLDER: MAP EFFORT >>
#set_db syn_opt_effort        << PLACEHOLDER: OPT EFFORT >>

set_db leakage_power_effort high

set_db hdl_max_memory_address_range 3200000000

set_db information_level 9
#set_db hdl_preserve_unused_registers true

set_db hdl_undriven_signal_value x
set_db hdl_undriven_output_port_value x
set_db hdl_unconnected_input_port_value x
#get_db delete_unloaded_insts false

set_db message:GLO-32 .truncate false

# set_db  lp_clock_gating_infer_enable  true
# set_db  lp_clock_gating_prefix  {CLKGATE}
# set_db  lp_insert_clock_gating  true

set hdl_bidirectional_assign false
#set_db init_blackbox_for_undefined true
#set_db hdl_error_on_blackbox   true

# [stevo]: seems to cause lots of problems
# nope, just dies on r720-16
#set_db auto_super_thread false
#set_db super_thread_servers 0
set_db pbs_keep_tmp_dir 1
set_db super_thread_debug_directory st_debug
set_db heartbeat 300 

set_db hdl_error_on_blackbox   true

set_db ungroup_separator /

# [stevo]: retiming
set rt_subds [get_designs "*IntToFP* *FPToFP* FPUFMAPipe*"]
foreach subd $rt_subds {
  set_db $subd .retime true
  ####Uncomment to prevent registers from being moved across the subdesign boundaries
  set_db $subd .retime_hard_region true
}

set_db / .retime_verification_flow true

# Prevent pruning or restructuring of IO pads:
set_db [vfind / -hinst FFT2Pads]  .ungroup_ok false
set_db [vfind / -inst FFT2Pads/IOPAD*]  .preserve true

# don't touch these nets
set_db [vfind / -net FFT2Pads/rte]  .preserve true
set_db [vfind / -net FFT2Core/io_clkrxvin]  .preserve true
set_db [vfind / -net FFT2Core/io_clkrxvip]  .preserve true


#set_db  boundary_optimize_constant_hpins  false
#set_db  boundary_optimize_equal_opposite_hpins  false
#set_db   boundary_optimize_feedthrough_hpins  false
