#! /bin/tcsh
# Takes in top level design name as argument and
# # runs basic synthesis script
if (-d synth/PE) then
  rm -rf synth/PE
endif
mkdir synth/PE
cd synth/PE
dc_shell -f ../../scripts/dc_synthesize.tcl  -output_log_file dc.log
../../cutmodule.awk PE < ../../genesis_verif/garnet.sv > ../../genesis_verif/garnet.no_pe.sv
cd ../..
mv genesis_verif/garnet.no_pe.sv genesis_verif/garnet.sv
