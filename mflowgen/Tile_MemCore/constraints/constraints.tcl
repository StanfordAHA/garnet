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

# Spec-generated MemCores with a single bulk controller have no `mode`
# config port: lake's memtile_builder.py makes `mode` a real input port only
# when num_modes > 1, otherwise it collapses to an internal 1-bit var wired to
# 0 (see lake/lake/top/memtile_builder.py:175-184). The classic onyx MemCore
# has several controllers (UB/FIFO/SRAM) so mode[0]/mode[1] exist; a
# single-spec MemCore does not, and set_case_analysis on the missing pin aborts
# synthesis with TUI-61. Detect the port once and skip the mode case-analysis
# when it is absent — such designs have one fixed behavior, so the three
# constraint scenarios below all analyze the real (single-mode) logic.
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
