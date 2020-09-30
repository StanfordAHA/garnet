source inputs/rtl-scripts/soc_include_paths.tcl
source inputs/rtl-scripts/soc_design_files.tcl
source inputs/rtl-scripts/cgra_design_files.tcl
source inputs/rtl-scripts/pad_frame_design_files.tcl

set design_files [concat $soc_design_files $cgra_design_files $pad_frame_design_files]

#set_attr init_hdl_search_path $search_path

echo "DA WIDTH: ${::env(TLX_REV_DATA_LO_WIDTH)}"

if { $::env(soc_only) } {
  read_hdl -define {ARM_CODEMUX=1 NO_CGRA=1 TLX_FWD_DATA_LO_WIDTH=16 TLX_REV_DATA_LO_WIDTH=45} -sv $design_files
} else {
  read_hdl -define {ARM_CODEMUX=1 TLX_FWD_DATA_LO_WIDTH=16 TLX_REV_DATA_LO_WIDTH=45} -sv $design_files
}

elaborate $design_name
