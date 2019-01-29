#! bin/tcsh
setenv DESIGN $1
if (-d $1) then
  rm -rf $1
endif
dc_shell -o "$1_syn.log" -f ../scripts/synthesize.tcl

