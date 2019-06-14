#! /bin/tcsh
# Takes in top level design name as argument and
# # runs basic synthesis script
setenv DESIGN PE
setenv PWR_AWARE 0
if (-d synth/${DESIGN}) then
  rm -rf synth/${DESIGN}
endif
mkdir synth/${DESIGN}
cd synth/${DESIGN}
dc_shell -f ../../scripts/dc_synthesize.tcl 
#../../cutmodule.awk PE < ../../genesis_verif/garnet.sv > ../../genesis_verif/garnet.no_pe.sv
cd ../..
mv genesis_verif/garnet.no_pe.sv genesis_verif/garnet.sv
