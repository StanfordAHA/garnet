#=========================================================================
# designer_interface.tcl
#=========================================================================
# The designer_interface.tcl file is the first script run by PTPX (see the
# top of ptpx.tcl) and sets up ASIC design kit variables and inputs.
#
# Author : Christopher Torng
# Date   : May 20, 2019

set ptpx_design_name        cgra

#-------------------------------------------------------------------------
# Libraries
#-------------------------------------------------------------------------

set adk_dir                       ../netlist

set ptpx_additional_search_path   ../netlist
set ptpx_target_libraries         ../netlist/stdcells.db

set ptpx_extra_link_libraries     [join "
                                      [lsort [glob -nocomplain ../netlist/*.db]]
                                      [lsort [glob -nocomplain ../netlist/*.db]]
                                  "]

#-------------------------------------------------------------------------
# Inputs
#-------------------------------------------------------------------------

set ptpx_gl_netlist         ../netlist/design.vcs.v
set ptpx_sdc                ../netlist/design.pt.sdc
set ptpx_spef               ../netlist/design.spef.gz
set ptpx_saif               ../run.saif

# The strip path must be defined!
#
#   export strip_path = th/dut
#
# There must _not_ be any quotes, or read_saif will fail. This fails:
#
#   export strip_path = "th/dut"
#

set ptpx_strip_path         "top/dut"

puts "done"