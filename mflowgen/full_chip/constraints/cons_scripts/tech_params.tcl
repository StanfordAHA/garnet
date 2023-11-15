#-----------------------------------------------------------------------------
# Synopsys Design Constraint (SDC) File
#-----------------------------------------------------------------------------
# Purpose: Tech-related parameters
#------------------------------------------------------------------------------
#
#
# Author   : Gedeon Nyengele
# Date     : May 9, 2020
#------------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# Units
# -----------------------------------------------------------------------------

# set_units -time ps -capacitance pF

# -----------------------------------------------------------------------------
# Clock timing
# -----------------------------------------------------------------------------

# Clock jitter modelling (absolute values)
set clock_period_jitter             0.000 ;# Reduces clock period through uncertainty
set clock_dutycycle_jitter          0.000 ;# Adjusts clock source falling edge timing

# Setup/Hold margin (absolute values)
set hold_margin                     0.000 ;# Hold margin target (all corners)
set setup_margin                    0.000 ;# Setup margin target (all corners)

# -----------------------------------------------------------------------------
# Pre-CTS clock skew and latency estimates
# -----------------------------------------------------------------------------

set pre_cts_clock_skew_estimate     0.000
set pre_cts_clock_latency_estimate  0.000

# -----------------------------------------------------------------------------
# Input driving cell models
# -----------------------------------------------------------------------------

# Clock pins
set clock_driving_cell              $ADK_DRIVING_CELL

# All other inputs
set driving_cell                    $ADK_DRIVING_CELL

# -----------------------------------------------------------------------------
# Output loading models
# -----------------------------------------------------------------------------

set output_load                     $ADK_TYPICAL_ON_CHIP_LOAD

# -----------------------------------------------------------------------------
# Max capacitance
# -----------------------------------------------------------------------------

set max_capacitance                 [expr 1.00 * 1000]

# -----------------------------------------------------------------------------
# Transition time targets
# -----------------------------------------------------------------------------

set max_transition                  [expr 0.100 * 1000]

# Clock transition requirement
set max_clock_transition            [expr $max_transition /2.0 ]
