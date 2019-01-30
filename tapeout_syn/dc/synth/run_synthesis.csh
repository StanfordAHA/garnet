#! bin/tcsh
# Takes in top level design name as argument and
# runs basic synthesis script
setenv DESIGN $1
if (-d $1) then
  rm -rf $1
endif
mkdir $1
cd $1
dc_shell -o "$1_syn.log" -f ../../scripts/synthesize.tcl
cd ..

