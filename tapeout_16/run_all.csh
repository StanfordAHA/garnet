#! /bin/tcsh
# Takes in top level design name as argument and
# # runs basic synthesis script
setenv DESIGN $1
setenv PWR_AWARE $2
if (-d synth/$1) then
  rm -rf synth/$1
endif
mkdir synth/$1
cd synth/$1
if ("${1}" =~ Tile* ) then
    innovus -replay ../../scripts/layout_Tile.tcl
else
    innovus -replay ../../scripts/layout_${1}.tcl

source ../../scripts/run_ncsim_${1}.csh > NCSIM.LOG
cd ../..
