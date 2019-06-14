#! /bin/tcsh
# Takes in top level design name as argument and
# # runs basic synthesis script
setenv DESIGN $1
setenv PWR_AWARE $2
if (-d synth/$1) then
  rm -rf synth/$1
endif
mkdir synth/$1
if ("$DESIGN" == "Tile_PE") then
    ./run_dc_pe_synth.csh
endif
cd synth/$1
if ("$3" == "") then 
    genus -legacy_ui -f ../../scripts/synthesize.tcl
else
    cp ../../dummy.v .
    genus -legacy_ui -f ../../scripts/synthesize_top.tcl
endif
cd ../..
