#! /bin/tcsh
# Takes in top level design name as argument and
# # runs basic synthesis script
set echo

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
    genus -no_gui -legacy_ui -f ../../scripts/synthesize.tcl || exit 13
else
    cp ../../dummy.v .
    genus -no_gui -legacy_ui -f ../../scripts/synthesize_top.tcl || exit 13
endif
cd ../..
