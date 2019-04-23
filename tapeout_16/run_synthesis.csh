#! /bin/tcsh
# Takes in top level design name as argument and
# # runs basic synthesis script
setenv DESIGN $1
setenv PWR_AWARE 0
if (-d synth/$1) then
  rm -rf synth/$1
endif
mkdir synth/$1
cd synth/$1
if ("$2" == "") then
    /cad/cadence/GENUS17.21.000.lnx86/bin/genus -legacy_ui -f ../../scripts/synthesize.tcl
else
    cp ../../dummy.v .
    /cad/cadence/GENUS17.21.000.lnx86/bin/genus -legacy_ui -f ../../scripts/synthesize_top.tcl
endif
cd ../..
