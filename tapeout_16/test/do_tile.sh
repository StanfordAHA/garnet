#!/bin/bash

# VERBOSE=true or false
if   [ "$1" == "-v" ] ; then VERBOSE=true;  shift;
elif [ "$1" == "-q" ] ; then VERBOSE=false; shift;
fi

if [ "$VERBOSE" == "true"  ]
  then verbose_flag="-v"
  else verbose_flag="-q"
fi

# TILE=PE or TILE=MemCore
if [ "$1" == "" ] ; then
  echo ""
  echo "Usage: $0 [-v | -q] < PE | MemCore >"
  echo "Examples:"
  echo "  $0 PE"
  echo "  $0 -v PE"
  echo "  $0 MemCore"
  echo ""
  exit 13
fi
TILE=$1

# echo "I see '$0 $*'"
# echo "VERBOSE=$VERBOSE"


# Default =  do it all
do_package_check=true
do_gen=true
do_synthesis=true
do_layout=true

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

# buildkite log: Group and collapse your build output by echoing
# --- [group name] in your build output:
#     echo "--- A section of the build"
# If you want to have the group open by default, use +++ instead of ---:
#     echo "+++ A section of the build"
# echo -e "+++ Running \033[33mspecs\033[0m :cow::bell:"
# 
function header {
  # E.g. "header --- header message" => "--- 07:52 header message"
  pfx=$1; shift
  echo "$pfx `date +%H:%M` $*"
}

##############################################################################
if [ $VERBOSE == true ] ; then
    header --- notes
    cat test/do_pe.notes.txt
fi

##############################################################################
header --- SETUP
pwd
ls test
source test/install.sh_source


##############################################################################
header --- GENERATE GARNET VERILOG, PUT IT IN CORRECT FOLDER FOR SYNTH/PNR
set +x # no echo
if [ $do_gen != true ] ; then
    echo "Skipping generation phase b/c do_gen variable not 'true'"
    echo ""
else
    test/generate.sh $verbose_flag
fi

##############################################################################
header --- "BLOCK-LEVEL SYNTHESIS - ${TILE}"
##############################################################################
# From the README:
#   Block-Level Synthesis:
# 
#     Navigate to CGRAGenerator/hardware/tapeout_16 NOPE
#     Navigate to garnet/tapeout_16
# 
#     Ensure that a constraints file called
#     constraints_<NAME OF BLOCK>.tcl exists in scripts/
# 
#     Do ./run_synthesis.csh <NAME OF Block>
#     a. Memory tile: ./run_synthesis.csh Tile_MemCore
#     b. PE Tile: ./run_synthesis.csh Tile_PE

set +x # no echo
if [ $do_synthesis != true ] ; then
    echo "Skipping synthesis phase b/c do_synthesis variable not 'true'"
    echo ""
else
    set +x # no echo
    # Should already be in tapeout16
    echo "Now we are here: `pwd`"; echo ""

    nobuf='stdbuf -oL -eL'
    if [ $VERBOSE == true ] ; 
      then filter=($nobuf cat)
      else filter=($nobuf ./test/run_synthesis.filter)
    fi

    set -x # echo ON
    PWR_AWARE=1
    $nobuf ./run_synthesis.csh Tile_${TILE} $PWR_AWARE \
      | ${filter[*]} \
      || exit 13
    set +x # echo OFF
fi

header ---  "PNR FLOW FOR TILES (LAYOUT) - ${TILE}"
##############################################################################
# README again - finally - P&R Flow for Tiles:
#     Navigate to CGRAGenerator/hardware/tapeout_16
#     Do ./run_layout.csh <NAME OF TILE>(this will take some time to complete)
#     a. Memory tile: ./run_layout.csh Tile_MemCore
#     b. PE Tile: ./run_layout.csh Tile_PE

set +x # no echo
if [ $do_layout != true ] ; then
    echo "Skipping layout phase b/c do_layout variable not 'true'"
    echo ""
else
    set +x # no echo
    # Should already be in tapeout16 I think
    echo "Now we are here: `pwd`"; echo ""

    echo "ERROR/FIXME SHOULD NOT HAVE TO DO THIS!!!"
    echo "ERROR/FIXME below symlink should maybe prevent the following error:
  File '/sim/ajcars/garnet/tapeout_16/scripts/layout_Tile.tcl' line 64:
  ../Tile_MemCore/results_syn/final_area.rpt: No such file or directory.

"
    set +x # echo OFF
    t16synth=/sim/ajcars/aha-arm-soc-june-2019/components/cgra/garnet/tapeout_16/synth

    # Must have both Mem and PE synthesized for this to work!
    for t in PE MemCore; do
        if ! test -d synth/Tile_${t} ; then
          echo "  Cannot find synth/Tile_${t}/ - I will fix it for you"
          cd synth
            ln -s $t16synth/Tile_${t}
            ls -ld Tile_${t} | fold -sw 100
          cd ..
          pwd
        fi
    done

    f=Tile_${TILE}/results_syn/final_area.rpt
    if ! test -f synth/$f; then
        echo "  Cannot find final_area.rpt - giving up"
    fi
    echo ""

    set +x # echo OFF
    nobuf='stdbuf -oL -eL'
    if [ $VERBOSE == true ]
      then filter=cat # default
      else filter=./test/run_layout.filter
    fi
    set -x # echo ON

    PWR_AWARE=1
    $nobuf ./run_layout.csh Tile_${TILE} $PWR_AWARE \
      | $nobuf $filter \
      || exit 13
    set +x # echo OFF

fi

##############################################################################
# Done?
header +++ FINAL SUMMARY

echo ""
echo "SYNTHESIS"
s=synth/Tile_${TILE}/genus.log
sed -n '/QoS Summary/,/Total Instances/p' $s
echo ""
echo "LAYOUT"
echo 'grep "DRC violations" synth/Tile_${TILE}/innovus.logv | tail -n 1'
echo 'grep "Message Summary" synth/Tile_${TILE}/innovus.logv | tail -n 1'
echo ""
grep "DRC violations"  synth/Tile_${TILE}/innovus.logv | tail -n 1
grep "Message Summary" synth/Tile_${TILE}/innovus.logv | tail -n 1

# Sample output:
# --- FINAL SUMMARY
# 
# SYNTHESIS
# QoS Summary for Tile_PE
# ================================================================================
# Metric                          final
# ================================================================================
# Slack (ps):                         0
#   R2R (ps):                         0
#   I2R (ps):                       168
#   R2O (ps):                         0
#   I2O (ps):                       168
#   CG  (ps):                     1,430
# TNS (ps):                           0
#   R2R (ps):                         0
#   I2R (ps):                         0
#   R2O (ps):                         0
#   I2O (ps):                         0
#   CG  (ps):                         0
# Failing Paths:                      0
# Cell Area:                      3,410
# Total Cell Area:                3,410
# Leaf Instances:                 7,593
# Total Instances:                7,593
#
# LAYOUT 
# [08/21 10:50:06  24968s] #Total number of DRC violations = 0
# [08/21 10:50:48  25032s] *** Message Summary: 30072 warning(s), 9 error(s)

echo "
do_pe.sh -------------------------------------------------------------
do_pe.sh DONE!
do_pe.sh `date` - `pwd`
"


##############################################################################
# OLD - see old/do_pe.sh.old
##############################################################################

