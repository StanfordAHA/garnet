#! /bin/tcsh
# Takes in top level design name as argument and
# # runs basic synthesis script
set echo

pwd
ls 
ls synth
ls synth/$1

setenv DESIGN $1
setenv PWR_AWARE $2
cd synth/$1


pwd
ls ../../scripts
ls ../../scripts/layout_Tiles.tcl
head ../../scripts/layout_Tiles.tcl



if ("${1}" =~ Tile* ) then
    innovus -no_gui -replay ../../scripts/layout_Tile.tcl
else
    innovus -replay ../../scripts/layout_${1}.tcl
endif
cd ../..
