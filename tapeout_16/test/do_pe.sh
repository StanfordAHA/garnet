#!/bin/bash

VERBOSE=true
VERBOSE=false

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
function subheader {
  pfx=$1; shift
  echo "------------------------------------------------------------------------"
  echo "$*"
}

##############################################################################
if [ $VERBOSE == true ] ; then
    header --- notes
    cat test/do_pe.notes.txt
fi

header --- SETUP
# Optional sanity checks
if [ $do_package_check == true ] ; then

  ##############################################################################
  subheader +++ VERIFY PYTHON VERSION AND PACKAGES

  # Check for python3.7 FIXME I'm sure there's a better way... :(
  # ERROR: Package 'peak' requires a different Python: 3.6.8 not in '>=3.7' :(
  v=`python3 -c 'import sys; print(sys.version_info[0]*1000+sys.version_info[1])'`
  echo "Found python version $v -- should be at least 3007"
  if [ $v -lt 3007 ] ; then
    echo ""; echo "ERROR found python version $v -- should be 3007"; exit 13
  fi
  echo ""

  subheader +++ VERIFY PYTHON PACKAGE REQUIREMENTS
  ##############################################################################
  # Check requirements
  # From garnet README:
  #   Install python dependencies
  #   $ pip install -r requirements.txt  # install python dependencies
  if [ $VERBOSE == true ];
    then test/requirements_check.sh -v || exit 13
    else test/requirements_check.sh -q || exit 13
  fi
  echo ""
fi

##############################################################################
subheader +++ MODULE LOAD REQUIREMENTS
source test/module_loads.sh -v
echo ""


##############################################################################
# Need to know that innovus is not throwing errors!!!
subheader +++ VERIFYING CLEAN INNOVUS
echo ""; 
echo "innovus -no_gui -execute exit"
nobuf='stdbuf -oL -eL'
if [ $VERBOSE == true ] ; 
  then filter=($nobuf cat)
  else filter=($nobuf egrep 'Version|ERROR|Summary')
fi

# It leaves little turds, so use a temp directory
# (note "--- " has special meaning in kite logs...)
mkdir tmp.$$; cd tmp.$$
  $nobuf innovus -no_gui -execute exit |& $nobuf tee tmp.iout \
    | $nobuf sed 's/^--- /^=== /' \
    | ${filter[*]}
  grep ERROR tmp.iout > /dev/null && ierr=true || ierr=false
cd ..; /bin/rm -rf tmp.$$
if [ $ierr == true ] ; then
    echo ""
    echo "ERROR looks like innovus install is not clean!"
    exit 13
fi



header --- GENERATE GARNET VERILOG, PUT IT IN CORRECT FOLDER FOR SYNTH/PNR
##############################################################################
# From the README:
# To Generate Garnet Verilog and put it in the correct folder for synthesis and P&R:
# 
#     Navigate to CGRAGenerator/hardware/tapeout_16
#     Do ./gen_rtl.sh
# 
# Copied gen_rtl.sh contents below...
# echo -e "--- generate"
set +x # no echo
if [ $do_gen != true ] ; then
    echo "Skipping generation phase b/c do_gen variable not 'true'"
    echo ""
else
    set +x # echo OFF
    if [ -d "genesis_verif/" ]; then
        "Found (and deleted) existing verilog `pwd`/genesis_verif/"
        rm -rf genesis_verif
    fi
    cd ../; echo "Now we are here: `pwd`"
    if [ -d "genesis_verif/" ]; then
        "Found (and deleted) existing verilog `pwd`/genesis_verif/"
        rm -rf genesis_verif
    fi

    echo ""
    echo "OMG are you kidding me."
    echo "coreir only works if /usr/local/bin comes before /usr/bin."
    echo 'export PATH=/usr/local/bin:$PATH'
    echo ""
    export PATH=/usr/local/bin:$PATH

    # This filter keeps Genesis output
    # "--- Genesis Is Starting Work On Your Design ---"
    # from being an expandable category in kite log =>
    # "=== Genesis Is Starting Work On Your Design ==="
    dash_filter='s/^--- /=== /;s/ ---$/ ===/'

    nobuf='stdbuf -oL -eL'
    function filter {
      set +x # echo OFF
      VERBOSE=true
      if [ $VERBOSE == true ] ; 
        then $nobuf cat $1
        else $nobuf egrep 'from\ module|^Running' $1 \
           | $nobuf sed '/^Running/s/ .input.*//'
      fi
    }

    ##############################################################################
    # THE MAIN EVENT - generation
    set -x # echo ON
    $nobuf python3 garnet.py --width 32 --height 16 -v --no_sram_stub \
      |& $nobuf sed "$dash_filter" \
      |& $nobuf tee do_gen.log \
      |& filter || exit
    set +x # echo OFF

    # |& $nobuf cat || exit 13

    echo ""
    echo Checking for errors
    grep -i error do_gen.log
    echo ""

    if ! test -f garnet.v; then
      echo ERROR oops where is garnet.v
      exit 13
    else
      echo "Now we are here: `pwd`"
      set -x # echo ON
      cp garnet.v genesis_verif/garnet.sv
      cp -r genesis_verif/ tapeout_16/
      set +x # echo OFF
    fi

    # POP BACK
    echo cd tapeout_16/; cd tapeout_16/
    echo "Now we are here: `pwd`"
    echo ""
fi


TILE=PE      # TILE=MemCore
header --- "BLOCK-LEVEL SYNTHESIS - ${TILE}"
##############################################################################
# README again - Block-Level Synthesis:
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

