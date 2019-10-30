#! /bin/tcsh
# Takes in top level design name as argument and
# # runs basic synthesis script
set echo

setenv DESIGN $1
setenv PWR_AWARE $2

cd synth/$1; pwd


if ("${1}" =~ Tile* ) then
    # Oops github script does not seem to work, use alex script instead
    set s=../../scripts/layout_Tile.tcl
    # set s=/sim/ajcars/garnet/tapeout_16/scripts/layout_Tile.tcl
else
    set s=../../scripts/layout_${1}.tcl
endif

# echo tcl commands as they execute; also, quit when done (!)
set wrapper=/tmp/layout_Tile.tcl.$$
echo "source -verbose $s" > $wrapper
echo "exit" >> $wrapper
set s=$wrapper

# Take out the traaaaash
if ($?BUILDKITE) then
  ls -l innovus.{cmd,log}* || echo no trash
  mv innovus.{cmd,log}* /tmp || echo no trash
endif

# innovus -no_gui -replay ../../scripts/layout_Tile.tcl
# OR innovus -replay ../../scripts/layout_${1}.tcl
innovus -no_gui -abort_on_error -replay $s || exit 13


# Pretty sure this (below) does nothing useful, since we are inside a script!
# cd ../..
