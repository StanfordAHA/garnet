#=========================================================================
# designer_interface.tcl
#=========================================================================
# The designer_interface.tcl file is the first script run by PTPX (see the
# top of ptpx.tcl) and sets up ASIC design kit variables and inputs.
#
# Author : Christopher Torng
# Date   : May 20, 2019

set ptpx_design_name        $::env(design_name)

#-------------------------------------------------------------------------
# Libraries
#-------------------------------------------------------------------------

set adk_dir                       inputs/adk

set ptpx_additional_search_path   $adk_dir
set ptpx_target_libraries         stdcells.db

set ptpx_extra_link_libraries     [join "
                                      [glob -nocomplain inputs/*.db]
                                      [glob -nocomplain inputs/adk/*.db]
                                  "]

# get rid of corner libs
set corner_libs                   [glob -nocomplain inputs/adk/*bc*.db]
foreach bc_lib $corner_libs {
    set ptpx_extra_link_libraries [lsearch -all -inline -not -exact $ptpx_extra_link_libraries $bc_lib]
}

#-------------------------------------------------------------------------
# Inputs
#-------------------------------------------------------------------------

set ptpx_gl_netlist         inputs/design.v

set ptpx_sdc                inputs/design.sdc
set ptpx_spef               inputs/design.spef
set ptpx_saif               inputs/run.saif

# The strip path must be defined!
#
#   export strip_path = th/dut
#
# There must _not_ be any quotes, or read_saif will fail. This fails:
#
#   export strip_path = "th/dut"
#

set ptpx_strip_path         $::env(strip_path)

puts "done"


