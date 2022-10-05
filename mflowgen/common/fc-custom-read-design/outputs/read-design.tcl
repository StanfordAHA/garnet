source inputs/rtl-scripts/soc_include_paths.tcl
source inputs/rtl-scripts/soc_design_files.tcl
source inputs/rtl-scripts/cgra_design_files.tcl
source inputs/rtl-scripts/pad_frame_design_files.tcl

set design_files [concat $soc_design_files $cgra_design_files $pad_frame_design_files]

#set_attr init_hdl_search_path $search_path

#
# Step Parameters
#
puts "\[Read Design\] soc_only = $::env(soc_only)"
puts "\[Read Design\] INCLUDE_XGCD = $::env(INCLUDE_XGCD)"
puts "\[Read Design\] TLX_FWD_DATA_LO_WIDTH = $::env(TLX_FWD_DATA_LO_WIDTH)"
puts "\[Read Design\] TLX_REV_DATA_LO_WIDTH = $::env(TLX_REV_DATA_LO_WIDTH)"

#
# Design Macro Definitions
#
set design_macro_defs [list]

#
# TLX Port Partitioning
#

lappend design_macro_defs TLX_FWD_DATA_LO_WIDTH=$::env(TLX_FWD_DATA_LO_WIDTH)
lappend design_macro_defs TLX_REV_DATA_LO_WIDTH=$::env(TLX_REV_DATA_LO_WIDTH)

#
# CGRA RTL Exclusion
#
if { $::env(soc_only) } {
    lappend design_macro_defs NO_CGRA=1
}

#
# XGCD RTL Exclusion
#
if { !$::env(INCLUDE_XGCD) } {
    lappend design_macro_defs NO_XGCD=1
}

#
# Read Design RTL
#
read_hdl -define $design_macro_defs -sv $design_files

#
# Elaborate Design
#
elaborate $design_name
