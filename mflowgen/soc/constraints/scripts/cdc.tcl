#-----------------------------------------------------------------------------
# Synopsys Design Constraint (SDC) File
#-----------------------------------------------------------------------------
# Purpose: Constrain CDC
#------------------------------------------------------------------------------
#
# Author   : Gedeon Nyengele
# Date     : May 8, 2020
#------------------------------------------------------------------------------

set_clock_groups -asynchronous -group {dp_jtag_clk} -group {sys_clk}
set_clock_groups -asynchronous -group {cgra_jtag_clk} -group {sys_clk}
