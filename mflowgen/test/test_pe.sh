#!/bin/bash
function where_this_script_lives {
  # Where this script lives
  scriptpath=$0      # E.g. "build_tarfile.sh" or "foo/bar/build_tarfile.sh"
  scriptdir=${0%/*}  # E.g. "build_tarfile.sh" or "foo/bar"
  if test "$scriptdir" == "$scriptpath"; then scriptdir="."; fi
  # scriptdir=`cd $scriptdir; pwd`
  (cd $scriptdir; pwd)
}
script_home=`where_this_script_lives`

# setup assumes this script lives in garnet/mflowgen/test/
build=/sim/$USER
garnet=`cd $script_home/../..; pwd`

# mflowgen
test  -d $build         || mkdir $build
test  -d $build/mflowgen || git clone https://github.com/cornell-brg/mflowgen.git
mflowgen=$build/mflowgen

# tsmc16 adk
cd $mflowgen/adks
test -d tsmc16-adk || git clone http://gitlab.r7arm-aha.localdomain/alexcarsello/tsmc16-adk.git
test -d tsmc16     || ln -s tsmc16-adk tsmc16

# Tile_PE
module=Tile_PE
if test -d $mflowgen/$module; then
    echo "oops $mflowgen/$module exists"
    echo "giving up already love ya bye-bye"
    exit 13
fi
mkdir $mflowgen/$module; cd $mflowgen/$module
../configure --design $garnet_repo/mflowgen/Tile_PE

