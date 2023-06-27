#!/bin/bash

########################################################################
# TODO want option to run 32x16 run maybe?
# - --4x2 or something maybe
# - or maybe "rtl-gold-check <amber|onyx> <--4x2 | --32x16>"


########################################################################
# --help switch

cmd=$0

HELP="
DESCRIPTION: Builds RTL for a 4x2 amber or onyx SoC, compares to reference build.

USAGE:
   $cmd amber      # Build and compare amber RTL
   $cmd onyx       # Build and compare onyx RTL

EXAMPLE
   $cmd amber && echo PASS || echo FAIL

"
[ "$1" == "--help" ] && echo "$HELP" && exit

########################################################################
# Script is designed to work from inside a docker container

if ! test -e aha; then
  echo 'ERROR cannot find root directory "/aha"'
  echo 'Must be inside aha docker container for script to work'
  exit 13
fi

export GARNET_HOME=/aha/garnet
echo "--- Found GARNET_HOME=$GARNET_HOME"

########################################################################
# Assemble the generation command-lie flags, env vars, etc.

# width=32  # slow 32x16
width=4     # quick 4x2
height=$((width/2))

# FIXME should really use garnet's gen_rtl.sh to generate the RTL and flags etc.
# This would require some kind of --no-docker flag for gen_rtl.sh or some such...

# RTL-build flags
flags="--width $width --height $height --pipeline_config_interval 8 -v --glb_tile_mem_size 256"

export WHICH_SOC=$1
ref=$1-4x2.v

# Amber needs a slightly different versions for some of the submodules
# Onyx needs extra gen flags

if [ "$1" == "amber" ]; then
    # Update docker to match necessary amber environment
    $GARNET_HOME/mflowgen/common/rtl/gen_rtl.sh -u | tee tmp-amber-updates.sh
    bash -c 'set -x; source tmp-amber-updates.sh'

elif [ "$1" == "onyx" ]; then
    flags="$flags --rv --sparse-cgra --sparse-cgra-combined"

else echo "$HELP" && exit 13; fi


########################################################################
echo '--- RTL test BEGIN ($1)' `date`
echo "WHICH_SOC: $WHICH_SOC"
echo "FLAGS: $flags"

# FIXME: this basically duplicates what is done by gen_rtl.sh;
# TODO should build/fix some kind of "build-rtl-only" for
# $GARNET_HOME/mflowgen/common/rtl/gen_rtl.sh and call that instead,
# like we do above for submodule updates.

# Prep/clean
cd /aha
rm -rf garnet/genesis_verif
rm -f  garnet/garnet.v

# Build new rtl
source /aha/bin/activate; # Set up the build environment
aha garnet $flags

# Assemble final design.v
cd /aha/garnet
cp garnet.v genesis_verif/garnet.v
cat genesis_verif/* > design.v
cat global_buffer/systemRDL/output/glb_pio.sv >> design.v
cat global_buffer/systemRDL/output/glb_jrdl_decode.sv >> design.v
cat global_buffer/systemRDL/output/glb_jrdl_logic.sv >> design.v
cat global_controller/systemRDL/output/*.sv >> design.v

# For better or worse: I put this in gen_rtl.sh
# Hack it up! FIXME should use same mechanism as onyx...define AO/AN_CELL
# Also see: garnet/mflowgen/common/rtl/gen_rtl.sh, gemstone/tests/common/rtl/{AN_CELL.sv,AO_CELL.sv}
cat design.v \
    | sed 's/AN_CELL inst/AN2D0BWP16P90 inst/' \
    | sed 's/AO_CELL inst/AO22D0BWP16P90 inst/' \
          > /tmp/tmp.v
mv -f /tmp/tmp.v design.v

printf "\n"


########################################################################
echo "+++ Compare result to reference build"

# Reference designs are gzipped to save space
test -f $ref && rm $ref

# I guess the most recent cd left us in "/aha/garnet" :(

# refdir=../aha/bin/ref
refdir=/aha/garnet/bin/ref
cp $refdir/$ref.gz . || exit 13
gunzip $ref.gz
f1=design.v; f2=$ref

printf "\n"
echo "Comparing `cat $f1 | wc -l` lines of $f1"
echo "versus    `cat $f2 | wc -l` lines of $f2"
printf "\n"

alias vcompare=/aha/garnet/bin/rtl-goldcompare.sh

echo "/aha/garnet/bin/rtl-goldcompare.sh $f1 $f2"
# ndiffs=`diff -Bb -I Date $f1 $f2 | wc -l`
ndiffs=`vcompare $f1 $f2 | wc -l`
if [ "$ndiffs" != "0" ]; then

    # ------------------------------------------------------------------------
    # TEST FAILED

    printf "Test FAILED with $ndiffs diffs\n\n"
    printf "Top 40 diffs:"
    # diff -I Date <(vcompare $f1) <(vcompare $f2) | head -40
    vcompare $f1 $f2 | head -40
    exit 13
fi

echo "Test PASSED"
