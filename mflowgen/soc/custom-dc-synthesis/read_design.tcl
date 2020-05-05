source inputs/rtl-scripts/soc_include_paths.tcl
source inputs/rtl-scripts/soc_design_files.tcl
source inputs/rtl-scripts/cgra_design_files.tcl
source inputs/rtl-scripts/pad_frame_design_files.tcl

set design_files [concat $soc_design_files $cgra_design_files $pad_frame_design_files]

echo "DA WIDTH: ${::env(TLX_REV_DATA_LO_WIDTH)}"

if { $::env(soc_only) } {
  if { ![analyze -define {ARM_CODEMUX=1 NO_CGRA=1 TLX_FWD_DATA_LO_WIDTH=16 TLX_REV_DATA_LO_WIDTH=45} -format sverilog $design_files] } { exit 1 }
} else {
  if { ![analyze -define {ARM_CODEMUX=1 TLX_FWD_DATA_LO_WIDTH=16 TLX_REV_DATA_LO_WIDTH=45} -format sverilog $design_files] } { exit 1 }
}

if {[file exists [which setup-design-params.txt]]} {
  elaborate $dc_design_name -file_parameters setup-design-params.txt
  rename_design $dc_design_name* $dc_design_name
} else {
  elaborate $dc_design_name
}
