# ==============================================================================
# Clock Setup
# ==============================================================================
#
# The system has the following real clocks:
#   - master clock      (IN)      : used by most of the SoC
#   - cgra clock        (IN)      : used by the CGRA
#   - dap clock         (IN)      : used by CoreSight
#   - trace clock       (OUT)     : output trace clock
#   - TLX fwd clock     (IN)      : used by fwd tlx logic
#   - TLX fwd ref clk   (OUT)     : output reference clock for TLX fwd channel
#   - TLX rev clock     (IN)      : used by reverse tlx logic
#
# The system has the following virtual clocks:
#   - TLX virtual rev clk         : used to constrain output signals on rev channel
#   - master virtual clock        : used to constrain output signals in master clock domain
#   - dap virtual clock           : used to constrain output signals in dap clock domain
# ==============================================================================

# Clock Names
set clock_names   [list master_clock \
                        cgra_clock \
                        dap_clock \
                        tlx_fwd_clock \
                        tlx_rev_clock \
                  ]
                        #trace_clock
set design_clocks [concat $clock_names [list \
                          Vmaster_clock \
                          Vtlx_rev_clock \
                          Vdap_clock \
                  ]]

# PARAMETER: clock period
set clock_period(master_clock)                  200.0
set clock_period(cgra_clock)                    200.0
set clock_period(dap_clock)                     200.0
set clock_period(trace_clock)                   200.0
set clock_period(tlx_fwd_clock)                 200.0
set clock_period(tlx_rev_clock)                 200.0

# PARAMETER: clock port
set clock_port(master_clock)                    master_clk_i
set clock_port(cgra_clock)                      cgra_clk_i
set clock_port(dap_clock)                       dap_tck_i
set clock_port(trace_clock)                     trace_clk_o
set clock_port(tlx_fwd_clock)                   tlx_fwd_clk_ref_i
set clock_port(tlx_rev_clock)                   tlx_rev_clk_ref_i

# PARAMETER: pre-cts skew estimate
set clock_skew(master_clock)                    0.00
set clock_skew(cgra_clock)                      0.00
set clock_skew(dap_clock)                       0.00
set clock_skew(trace_clock)                     0.00
set clock_skew(tlx_fwd_clock)                   0.00
set clock_skew(tlx_rev_clock)                   0.00

# PARAMETER: clock duty cycle jitter
set clock_jitter(master_clock)                  0.02
set clock_jitter(cgra_clock)                    0.02
set clock_jitter(dap_clock)                     0.02
set clock_jitter(trace_clock)                   0.02
set clock_jitter(tlx_fwd_clock)                 0.02
set clock_jitter(tlx_rev_clock)                 0.02

# PARAMETER: clock extra setup margin
set clock_extra_setup(master_clock)             0.00
set clock_extra_setup(cgra_clock)               0.00
set clock_extra_setup(dap_clock)                0.00
set clock_extra_setup(trace_clock)              0.00
set clock_extra_setup(tlx_fwd_clock)            0.00
set clock_extra_setup(tlx_rev_clock)            0.00

# PARAMETER: clock extra hold margin
set clock_extra_hold(master_clock)              0.00
set clock_extra_hold(cgra_clock)                0.00
set clock_extra_hold(dap_clock)                 0.00
set clock_extra_hold(trace_clock)               0.00
set clock_extra_hold(tlx_fwd_clock)             0.00
set clock_extra_hold(tlx_rev_clock)             0.00

# PARAMETER: pre-cts clock maximum latency
set clock_max_latency(master_clock)             0.00
set clock_max_latency(cgra_clock)               0.00
set clock_max_latency(dap_clock)                0.00
set clock_max_latency(trace_clock)              0.00
set clock_max_latency(tlx_fwd_clock)            0.00
set clock_max_latency(tlx_rev_clock)            0.00

# PARAMETER: pre-cts clock minimum latency
set clock_min_latency(master_clock)             0.00
set clock_min_latency(cgra_clock)               0.00
set clock_min_latency(dap_clock)                0.00
set clock_min_latency(trace_clock)              0.00
set clock_min_latency(tlx_fwd_clock)            0.00
set clock_min_latency(tlx_rev_clock)            0.00

# PARAMETER: clock setup uncertainty
set clock_uncertainty_setup(master_clock)      [expr  $clock_skew(master_clock) + \
                                                      $clock_jitter(master_clock) + \
                                                      $clock_extra_setup(master_clock) \
                                               ]
set clock_uncertainty_setup(cgra_clock)        [expr  $clock_skew(cgra_clock) + \
                                                      $clock_jitter(cgra_clock) + \
                                                      $clock_extra_setup(cgra_clock) \
                                               ]
set clock_uncertainty_setup(dap_clock)         [expr  $clock_skew(dap_clock) + \
                                                      $clock_jitter(dap_clock) + \
                                                      $clock_extra_setup(dap_clock) \
                                               ]
set clock_uncertainty_setup(trace_clock)       [expr  $clock_skew(trace_clock) + \
                                                      $clock_jitter(trace_clock) + \
                                                      $clock_extra_setup(trace_clock) \
                                               ]
set clock_uncertainty_setup(tlx_fwd_clock)     [expr  $clock_skew(tlx_fwd_clock) + \
                                                      $clock_jitter(tlx_fwd_clock) + \
                                                      $clock_extra_setup(tlx_fwd_clock) \
                                               ]
set clock_uncertainty_setup(tlx_rev_clock)     [expr  $clock_skew(tlx_rev_clock) + \
                                                      $clock_jitter(tlx_rev_clock) + \
                                                      $clock_extra_setup(tlx_rev_clock) \
                                               ]
# PARAMETER: clock hold uncertainty
set clock_uncertainty_hold(master_clock)      [expr  $clock_jitter(master_clock) + \
                                                     $clock_extra_hold(master_clock) \
                                              ]
set clock_uncertainty_hold(cgra_clock)        [expr  $clock_jitter(cgra_clock) + \
                                                     $clock_extra_hold(cgra_clock) \
                                              ]
set clock_uncertainty_hold(dap_clock)         [expr  $clock_jitter(dap_clock) + \
                                                     $clock_extra_hold(dap_clock) \
                                              ]
set clock_uncertainty_hold(trace_clock)       [expr  $clock_jitter(trace_clock) + \
                                                     $clock_extra_hold(trace_clock) \
                                              ]
set clock_uncertainty_hold(tlx_fwd_clock)     [expr  $clock_jitter(tlx_fwd_clock) + \
                                                     $clock_extra_hold(tlx_fwd_clock) \
                                              ]
set clock_uncertainty_hold(tlx_rev_clock)     [expr  $clock_jitter(tlx_rev_clock) + \
                                                     $clock_extra_hold(tlx_rev_clock) \
                                              ]

# ==============================================================================
# Clock Creation
# ==============================================================================

foreach clock_name $clock_names {
  create_clock -name $clock_name -period $clock_period($clock_name) \
    [get_ports $clock_port($clock_name)]
  set_clock_latency -max $clock_max_latency($clock_name) [get_clocks $clock_name]
  set_clock_latency -min $clock_min_latency($clock_name) [get_clocks $clock_name]
  set_clock_uncertainty -setup $clock_uncertainty_setup($clock_name) [get_clocks $clock_name]
  set_clock_uncertainty -hold $clock_uncertainty_hold($clock_name) [get_clocks $clock_name]
}

# TLX FWD Reference Clock
create_generated_clock -name tlx_fwd_ref_clock -divide_by 1 -source [get_ports $clock_port(tlx_fwd_clock)] \
  [get_ports tlx_fwd_clk_ref_o]

# Virtual Master Clock
create_clock -name Vmaster_clock -period $clock_period(master_clock)

# Virtual DAP Clock
create_clock -name Vdap_clock -period $clock_period(dap_clock)

# Virtual TLX REV Clock
create_clock -name Vtlx_rev_clock -period $clock_period(tlx_rev_clock)

# ==============================================================================
# Clock Path Exceptions / False Paths
# ==============================================================================

# from master clock
set false_paths(master_clock)             [list cgra_clock \
                                                dap_clock \
                                                tlx_fwd_clock \
                                                tlx_fwd_ref_clock \
                                                tlx_rev_clock \
                                                Vtlx_rev_clock \
                                                Vdap_clock \
                                          ]

# from cgra clock
set false_paths(cgra_clock)               [list master_clock \
                                                dap_clock \
                                                trace_clock \
                                                tlx_fwd_clock \
                                                tlx_fwd_ref_clock \
                                                tlx_rev_clock \
                                                Vmaster_clock \
                                                Vtlx_rev_clock \
                                                Vdap_clock \
                                          ]

# from dap clock
set false_paths(dap_clock)                [list master_clock \
                                                cgra_clock \
                                                trace_clock \
                                                tlx_fwd_clock \
                                                tlx_fwd_ref_clock \
                                                tlx_rev_clock \
                                                Vmaster_clock \
                                                Vtlx_rev_clock \
                                          ]

# from trace clock
set false_paths(trace_clock)              [list cgra_clock \
                                                dap_clock \
                                                tlx_fwd_clock \
                                                tlx_fwd_ref_clock \
                                                tlx_rev_clock \
                                                Vtlx_rev_clock \
                                                Vdap_clock \
                                          ]

# from tlx fwd clock
set false_paths(tlx_fwd_clock)            [list master_clock \
                                                cgra_clock \
                                                dap_clock \
                                                trace_clock \
                                                tlx_rev_clock \
                                                Vmaster_clock \
                                                Vtlx_rev_clock \
                                                Vdap_clock \
                                          ]

# from tlx fwd ref clock
set false_paths(tlx_fwd_ref_clock)        [list master_clock \
                                                cgra_clock \
                                                dap_clock \
                                                trace_clock \
                                                tlx_rev_clock \
                                                Vmaster_clock \
                                                Vtlx_rev_clock \
                                                Vdap_clock \
                                          ]

# from tlx rev clock
set false_paths(tlx_rev_clock)            [list master_clock \
                                                cgra_clock \
                                                dap_clock \
                                                trace_clock \
                                                tlx_fwd_clock \
                                                tlx_fwd_ref_clock \
                                                Vmaster_clock \
                                                Vdap_clock \
                                          ]

# from virtual master clock
set false_paths(Vmaster_clock)            [list cgra_clock \
                                                dap_clock \
                                                tlx_fwd_clock \
                                                tlx_fwd_ref_clock \
                                                tlx_rev_clock \
                                                Vtlx_rev_clock \
                                                Vdap_clock \
                                          ]

# from virtual tlx rev clock
set false_paths(Vtlx_rev_clock)           [list master_clock \
                                                cgra_clock \
                                                dap_clock \
                                                trace_clock \
                                                tlx_fwd_clock \
                                                tlx_fwd_ref_clock \
                                                Vmaster_clock \
                                                Vdap_clock \
                                          ]

# from virtual dap clock
set false_paths(Vdap_clock)               [list master_clock \
                                                cgra_clock \
                                                trace_clock \
                                                tlx_fwd_clock \
                                                tlx_fwd_ref_clock \
                                                tlx_rev_clock \
                                                Vmaster_clock \
                                                Vtlx_rev_clock \
                                          ]

foreach clock_name $design_clocks {
  set_false_path -from [get_clocks $clock_name] -to [get_clocks $false_paths($clock_name)]
}

# This constraint sets the load capacitance in picofarads of the
# output pins of your design.

set_load -pin_load $ADK_TYPICAL_ON_CHIP_LOAD [all_outputs]

# This constraint sets the input drive strength of the input pins of
# your design. We specifiy a specific standard cell which models what
# would be driving the inputs. This should usually be a small inverter
# which is reasonable if another block of on-chip logic is driving
# your inputs.

set_driving_cell -no_design_rule \
  -lib_cell $ADK_DRIVING_CELL [all_inputs]

# Make all signals limit their fanout

set_max_fanout 20 $dc_design_name

# Make all signals meet good slew

set_max_transition [expr 0.25*${dc_clock_period}] $dc_design_name

