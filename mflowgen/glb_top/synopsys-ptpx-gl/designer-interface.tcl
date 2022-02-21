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

set ptpx_gl_netlist         "inputs/design.vcs.v inputs/glb_tile.vcs.v"
if {$::env(PWR_AWARE) == "True"} {
    set ptpx_gl_netlist     "inputs/design.vcs.pg.v inputs/glb_tile.vcs.pg.v"
}
set ptpx_sdc                inputs/design.pt.sdc
set ptpx_spef               inputs/design.spef.gz
# set ptpx_saif               inputs/run.saif
set ptpx_fsdb               inputs/run.fsdb

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


