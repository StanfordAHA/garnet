#! /bin/tcsh
# Takes in top level design name as argument and
# # runs basic synthesis script
set echo

setenv DESIGN $1
setenv PWR_AWARE $2

cd synth/$1; pwd
if ("${1}" =~ Tile* ) then
    innovus -no_gui -replay ../../scripts/layout_Tile.tcl || exit 13
else
    innovus -replay ../../scripts/layout_${1}.tcl || exit 13
endif
cd ../..
