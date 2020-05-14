#-----------------------------------------------------------------------------
# Synopsys Design Constraint (SDC) File
#-----------------------------------------------------------------------------
# Purpose: Design Context
#------------------------------------------------------------------------------
#
#
# Author   : Gedeon Nyengele
# Date     : May 9, 2020
#------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
# Cells to not ungroup
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
# Identify High Fanout Nets
# ------------------------------------------------------------------------------
set_ideal_network -no_propagate ${reset_ports}

# ------------------------------------------------------------------------------
# Set design context
# ------------------------------------------------------------------------------

# Set the maximum fanout value on the design
set_max_fanout 40 ${dc_design_name}

# Set the maximum transition value on the design
set_max_transition $max_transition ${dc_design_name}

# Load all outputs with suitable capacitance
set_load $output_load [all_outputs]

# Drive input ports with a standard driving cell and input transition
set_driving_cell -no_design_rule \
                  -lib_cell ${driving_cell} \
                 [remove_from_collection [all_inputs] ${clock_ports}]

set_driving_cell -no_design_rule \
                 -lib_cell ${clock_driving_cell} \
                 ${clock_ports}

set_max_area 0
