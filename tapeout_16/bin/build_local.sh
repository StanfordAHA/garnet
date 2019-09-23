#!/bin/bash
# Uses buildkite scripts to run synthesis and layout locally

# VERBOSE currently unused I think
VERBOSE=false
if   [ "$1" == "-v" ] ; then VERBOSE=true;  shift;
elif [ "$1" == "-q" ] ; then VERBOSE=false; shift;
fi

TOP_ONLY=false
if [ "$1" == "--top_only" ] ; then TOP_ONLY=true;  shift;

# Little hack, builds minimal CGRA grid, doesn't seem to help anything much
# LITTLE=''
# if [ "$1" == "--LITTLE" ] ; then LITTLE="$1"; shift; fi

# Check to see if we're in the right place e.g. "tapeout_16" directory
# expr `pwd` : '.*/garnet/tapeout_16$' && rightplace=true || rightplace=false
expr `pwd` : '.*/tapeout_16$' > /dev/null && rightplace=true || rightplace=false
if [ $rightplace != true ] ; then
  echo ""
  echo "ERROR looks like you're in the wrong place"
  echo "- you are here:   `pwd`"
  echo "- should be here: .../tapeout_16"
  exit 13
fi

# Designate a cache directory CACHEDIR for staging different phases:
# 
# GEN.sh puts generated verilog in CACHEDIR/genesis_verif
# GEN.sh puts generated mem_cfg.txt, mem_synth.txt in CACHEDIR
# 
# SYN.sh fetches genesis_verif, mem_cfg.txt, mem_synth.txt from CACHEDIR
# SYN.sh copies synth/{append.csh,PE/,run_all.csh,Tile_MemCore/,Tile_PE/} to CACHEDIR
#
# TOP.sh on local machine fetches synth info from CACHEDIR
# TOP.sh on buildkite does not use CACHEDIR

# Use e.g. /tmp/cache-steveri as the cache directory CACHEDIR
set -x
export CACHEDIR=/tmp/cache-$USER

# TOP.sh will do this (maybe)
# # Copy contents of synth directory to local runspace
# ls $CACHEDIR/synth synth/
# cp -rp $CACHEDIR/synth/* synth/
# ls synth

# Hm okay let's hold off on this for now.
# [ -e $CACHEDIR ] && /bin/rm -rf $CACHEDIR
# mkdir -p $CACHEDIR

# Start at top level dir, just like buildkite would do
cd ..

if [ "$TOP_ONLY" == "false" ] ; then
    .buildkite/GEN.sh -v $LITTLE

    .buildkite/SYN.sh -q PE
    .buildkite/SYN.sh -q MemCore

    .buildkite/PNR.sh -q PE
    .buildkite/PNR.sh -q MemCore
fi

.buildkite/TOP.sh -q


# Later we can try this
# $nobuf .buildkite/SYN.sh -q PE | $nobuf awk '{print "PE: " $0}' &
# .buildkite/SYN.sh -q MemCore | $nobuf awk '{print "    Mem: " $0}' &


# Cleaning gup
/bin/rm -rf ./cache
