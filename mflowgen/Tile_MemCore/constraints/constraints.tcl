#=========================================================================
# Design Constraints File
#=========================================================================

# This constraint sets the target clock period for the chip in
# nanoseconds. Note that the first parameter is the name of the clock
# signal in your verlog design. If you called it something different than
# clk you will need to change this. You should set this constraint
# carefully. If the period is unrealistically small then the tools will
# spend forever trying to meet timing and ultimately fail. If the period
# is too large the tools will have no trouble but you will get a very
# conservative implementation.

# This script creates different timing constraints under different memory mode
# configurations.  The general flow is to define a scenario, read in a script
# containing generalized constraints for the designs, then provide overriding
# constraints in different operational modes.

set_units -time ns -capacitance pF

set common_cnst inputs/common.tcl

##############################
# Check for power aware
##############################
if $::env(PWR_AWARE) {
    source inputs/mem-constraints.tcl
}

# Which SoC?
if { [info exists ::env(WHICH_SOC)] } {
    set WHICH_SOC $::env(WHICH_SOC)
} else {
    set WHICH_SOC "onyx"
}

set module MemCore_inner_W_inst0
if { $WHICH_SOC == "amber" } { set module LakeTop_W_inst0 }

# The mode case-analysis below assumes a 2-bit mode[1:0] bus on
# MemCore_inner_W, which the classic onyx MemCore has (several controllers ->
# UB/FIFO/SRAM). Spec-generated MemCores do NOT: verified against real
# garnet.py RTL, MemCore_inner_W there declares `input logic mode` -- a 1-bit
# SCALAR (mode_excl carries the rest) -- so neither mode[0] nor mode[1] is a
# findable pin, and set_case_analysis on them aborts synthesis with TUI-61.
# (lake's memtile_builder.py sizes `mode` from num_modes; the spec memtiles we
# sweep land on the scalar form.) So detect mode[0] once and skip the
# case-analysis when it is absent -- those designs still synthesize; the three
# constraint scenarios below just analyze the real logic without pinning mode.
proc _obj_exists {name} {
    set found 0
    catch { if {[llength [get_pins $name]]  > 0} { set found 1 } }
    if {$found} { return 1 }
    catch { if {[llength [get_ports $name]] > 0} { set found 1 } }
    return $found
}
set has_mode [_obj_exists "MemCore_inst0/$module/mode\[0\]"]
if { !$has_mode } {
    puts "INFO: constraints.tcl: no 'mode' config port on MemCore_inst0/$module -- \
single-controller (spec) design; skipping mode case-analysis."
}

create_mode -name UNIFIED_BUFFER
set_constraint_mode UNIFIED_BUFFER

# Read common
source -echo -verbose ${common_cnst}

if { $has_mode } {
    set_case_analysis 0 MemCore_inst0/$module/mode[0]
    set_case_analysis 0 MemCore_inst0/$module/mode[1]
}

create_mode -name FIFO
set_constraint_mode FIFO

# Read common
source -echo -verbose ${common_cnst}

if { $has_mode } {
    set_case_analysis 1 MemCore_inst0/$module/mode[0]
    set_case_analysis 0 MemCore_inst0/$module/mode[1]
}

create_mode -name SRAM
set_constraint_mode SRAM

# Read common
source -echo -verbose ${common_cnst}

if { $has_mode } {
    set_case_analysis 0 MemCore_inst0/$module/mode[0]
    set_case_analysis 1 MemCore_inst0/$module/mode[1]
}
