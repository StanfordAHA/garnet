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
# Set design context
# ------------------------------------------------------------------------------

set clock_ports   [list   $port_names(btfy_jtag_clk) \
                          $port_names(tlx_rev_clk) \
                          $port_names(dp_jtag_clk) \
                          $port_names(cgra_jtag_clk) \
                          $port_names(master_clk) \
                  ]

# Set the maximum fanout value on the design
set_max_fanout 32 ${design_name}

# Set the maximum transition value on the design
set_max_transition $max_transition ${design_name}

# Load all outputs with suitable capacitance
set_load $output_load [all_outputs]

# Drive input ports with a standard driving cell and input transition
set_driving_cell -no_design_rule \
                  -lib_cell ${driving_cell} \
                 [remove_from_collection [all_inputs] ${clock_ports}]

set_driving_cell -no_design_rule \
                 -lib_cell ${clock_driving_cell} \
                 [get_ports ${clock_ports}]

#set_max_area 0
