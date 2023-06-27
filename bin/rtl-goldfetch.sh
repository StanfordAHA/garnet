#!/bin/bash

cmd=$0; HELP="
DESCRIPTION:
  Uses docker and current garnet version to build and fetch
  latest RTL, potentially to replace existing gold version.

USAGE:
  $cmd amber      # Build and compare amber RTL
  $cmd onyx       # Build and compare onyx RTL

EXAMPLE
  $cmd onyx
  cp /tmp/deleteme-goldfetch/onyx-4x2.v.gz $GARNET_HOME/bin/ref/
  gzip $GARNET_HOME/bin/ref/onyx-4x2.v

"
[ "$1" == "--help" ] && echo "$HELP" && exit
[ "$1" == "" ] && echo "$HELP" && exit
soc=$1  # "amber" or "onyx"

# Find GARNET_HOME, assuming this script lives in $GARNET_HOME/bin
function where_this_script_lives {
  local scriptpath=`realpath $cmd`       # Full path of script e.g. "/foo/bar/baz.sh"
  local scriptdir=${scriptpath%/*}       # Script dir e.g. "/foo/bar"
  scriptdir=$(cd $scriptdir; pwd)   # Get abs path instead of relative
  [ "$scriptdir" == `pwd` ] && scriptdir="."
  echo $scriptdir
}
script_home=`where_this_script_lives`
GARNET_HOME=$(cd $script_home/..; pwd)
# echo Found garnet home $GARNET_HOME

# Pull docker image and set up a container
image=stanfordaha/garnet:latest
container=gold-fetch-$$
docker pull $image
docker run -id --name $container --rm -v /cad:/cad $image bash
function dexec { docker exec $container /bin/bash -c "$*"; }

# Prepare a garnet clone
# Assume script is run seldom so little chance of clone collision etc.
GTMP=/tmp/deleteme-goldfetch
test -e $GTMP && /bin/rm -rf $GTMP
mkdir -p $GTMP
git clone $GARNET_HOME $GTMP/garnet

# Copy clone to docker and then delete local version
dexec "rm -rf /aha/garnet"
docker cp $GTMP/garnet $container:/aha/garnet;
/bin/rm -rf $GTMP/garnet

# Build the gold RTL and copy it to $GTMP
dexec "/aha/aha/bin/rtl-goldcheck.sh $soc" || echo RTL build FAILED
docker cp $container:/aha/garnet/design.v $GTMP/$soc-4x2.v
gzip $GTMP/$soc-4x2.v

# Clean up
docker kill $container || echo cannot kill container;

# Advertise final result
echo New RTL is here
ls -lh $GTMP/$soc-4x2.v.gz
echo " --- "
echo Compare to existing gold
ls -lh $GARNET_HOME/bin/ref/$soc-4x2.v.gz
echo " --- "
echo "$GARNET_HOME/bin/rtl-goldcompare.sh \\"
echo "  <(gunzip -c $GARNET_HOME/bin/ref/$soc-4x2.v.gz) \\"
echo "  <(gunzip -c $GTMP/$soc-4x2.v.gz) |& less"
