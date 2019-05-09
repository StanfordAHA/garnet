#! /bin/tcsh
# Takes in top level design name as argument and
# # runs basic synthesis script
setenv DESIGN $1
setenv PWR_AWARE $2
cd synth/$1
innovus -replay ../../scripts/layout_${1}.tcl
cd ../..
