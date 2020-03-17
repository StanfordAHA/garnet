source scripts/soc_include_paths.tcl
source scripts/soc_design_files.tcl
source scripts/cgra_design_files.tcl
source scripts/pad_frame_design_files.tcl

set design_files [concat $soc_design_files $cgra_design_files $pad_frame_design_files]

if { ![analyze -define ARM_CODEMUX=1 -format sverilog $design_files] } { exit 1 }
if {[file exists [which setup-design-params.txt]]} {
  elaborate $dc_design_name -file_parameters setup-design-params.txt
  rename_design $dc_design_name* $dc_design_name
} else {
  elaborate $dc_design_name
}

