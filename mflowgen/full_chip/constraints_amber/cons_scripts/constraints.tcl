#-----------------------------------------------------------------------------
# Synopsys Design Constraint (SDC) File
#-----------------------------------------------------------------------------
# Purpose: Design Constraints
#------------------------------------------------------------------------------
#
#
# Author   : Gedeon Nyengele
# Date     : May 9, 2020
#------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
# Tech Parameters
# ------------------------------------------------------------------------------
source -echo -verbose inputs/cons_scripts/tech_params.tcl

# ------------------------------------------------------------------------------
# Set-up Design Configuration Options
# ------------------------------------------------------------------------------
source -echo -verbose inputs/cons_scripts/design_info.tcl

# ------------------------------------------------------------------------------
# Clock Constraints
# ------------------------------------------------------------------------------
source -echo -verbose inputs/cons_scripts/clocks_0_params.tcl
source -echo -verbose inputs/cons_scripts/clocks_1_master.tcl
source -echo -verbose inputs/cons_scripts/clocks_2_sys.tcl
source -echo -verbose inputs/cons_scripts/clocks_3_tlx.tcl
source -echo -verbose inputs/cons_scripts/clocks_4_cgra.tcl
source -echo -verbose inputs/cons_scripts/clocks_5_periph.tcl
source -echo -verbose inputs/cons_scripts/clocks_6_jtag.tcl
source -echo -verbose inputs/cons_scripts/clocks_7_trace.tcl

# ------------------------------------------------------------------------------
# IO Constraints for Source-Sync Interfaces
# ------------------------------------------------------------------------------
source -echo -verbose inputs/cons_scripts/io.tcl
source -echo -verbose inputs/cons_scripts/pad_strength.tcl
source -echo -verbose inputs/cons_scripts/clocks_except_soc.tcl

# ------------------------------------------------------------------------------
# Constraints for paths between CGRA, GLB, GLC
# ------------------------------------------------------------------------------
source -echo -verbose inputs/cons_scripts/garnet_constraints.tcl

# ------------------------------------------------------------------------------
# Set Design Context
# ------------------------------------------------------------------------------
source -echo -verbose inputs/cons_scripts/design_context.tcl
