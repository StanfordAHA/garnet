#!/bin/bash

# Exit on error from any pipe stage of any command
set -eo pipefail

VERBOSE=false
if [ "$1" == "-v" ]; then VERBOSE=true;  shift; fi
if [ "$1" == "-q" ]; then VERBOSE=false; shift; fi

topdir=`pwd`

########################################################################
echo "--- MODULE LOAD REQUIREMENTS"
echo ""
set +x; source tapeout_16/test/module_loads.sh


##############################################################################
echo "--- GENESIS2 GENERATES PAD FRAME I GUESS"
set -x
cd $topdir/pad_frame
  # ./create_pad_frame.sh; 
  Genesis2.pl -parse -generate -top   Garnet_SoC_pad_frame \
                               -input Garnet_SoC_pad_frame.svp


########################################################################
# FETCH SYNTH COLLATERAL FROM PRIOR BUILD STAGES
set -x
if [ "$BUILDKITE" ]; then
  # Copy in the latest synth info from previous buildkite passes (PE, mem synth)
  # Copy cached collateral from synthesis step
  echo "--- FETCH SYNTH COLLATERAL FROM PRIOR BUILD STAGES"
  cd $topdir/tapeout_16
  echo "cp -rp $CACHEDIR/synth ."
  cp -rp $CACHEDIR/synth .
fi

# (From tapeout_16/README in 'tapeout' branch
# P&R Flow for Top:
#     Navigate to garnet/tapeout_16/synth/GarnetSOC_pad_frame
#     Type innovus -stylus to open the Innovus tool
#     Type source ../../scripts/top_flow_multi_vt.tcl

# # For now let's try using the collateral we generated on buildkite
# CACHEDIR=/sim/buildkite-agent/builds/cache
# 
# # (if buildkite) Copy cached collateral from synthesis step
# if [ "$BUILDKITE" ]; then
#   # Copy cached collateral from synthesis step
#   echo "cp -rp $CACHEDIR/synth ."
#   cp -rp $CACHEDIR/synth/* tapeout16_synth/
# fi



##############################################################################
##############################################################################
##############################################################################
# CURRENTLY NOT DOING THIS I THINK -
# Only using collateral from prev stages (see above)
# 
# echo "--- FETCH SYNTH COLLATERAL FROM ALEX DIR (?)"
# set -x
# cd $topdir/tapeout_16
# 
# ato=/sim/ajcars/aha-arm-soc-june-2019/components/cgra/garnet/tapeout_16/
# synth_src_sinal=$ato/synth_no_pass_through/GarnetSOC_pad_frame_multi_vt
# 
# synth_src=/sim/ajcars/aha-arm-soc-june-2019/implementation/synthesis/synth
# cp -rp $synth_src/GarnetSOC_pad_frame/ synth/
##############################################################################
##############################################################################
##############################################################################




##############################################################################
# **ERROR: (TCLCMD-989): cannot open SDC file
#   'results_syn/syn_out._default_constraint_mode_.sdc'...
# **ERROR: (IMPSE-110): File '../../scripts/viewDefinition_multi_vt.tcl'
#   line 1: 1.
# 
# Need...? Garnet synthesis info I guess...? ???
# synth_Garnet=/sim/ajcars/garnet/tapeout_16/synth/Garnet
# cp -rp $synth_Garnet/* .
# Nope! Copy GarnetSOC_pad_frame, see above


##############################################################################
# **ERROR: ...  Can not open file '../Tile_PE/pnr.lib' for library set
# **ERROR: ...  Can not open file '../Tile_MemCore/pnr.lib' for library set
# **ERROR: ...  File '../../scripts/viewDefinition_multi_vt.tcl' line 3
#
# (Oops forgot to save layout collateral to cache dir) - SOLVED maybe


########################################################################
# Type innovus -stylus to open the Innovus tool
# Type source ../../scripts/top_flow_multi_vt.tcl

##############################################################################
echo "--- PNR PREP"
set -x
# Navigate to garnet/tapeout_16/synth/GarnetSOC_pad_frame
# cd tapeout_16/synth/
# [ -d GarnetSOC_pad_frame ] || mkdir GarnetSOC_pad_frame
# cd GarnetSOC_pad_frame
cd $topdir/tapeout_16/synth/GarnetSOC_pad_frame

# # echo tcl commands as they execute; also, quit when done (!)
# tmpdir=`mktemp -d tmpdir.XXX`
# f=top_flow_multi_vt.tcl
# wrapper=$tmpdir/$f
# echo "source -verbose ../../scripts/$f" > $wrapper
# echo "redirect pnr.clocks {report_clocks}" >> $wrapper
# echo "exit" >> $wrapper
# echo ""

wrapper=../../scripts/top_garnet_redo.tcl



# PWR_AWARE=1
nobuf='stdbuf -oL -eL'

# innovus -stylus -no_gui -abort_on_error -replay $wrapper || exit 13

if [ "$VERBOSE" == true ];
  then filter=($nobuf cat)                          # VERBOSE
  else filter=($nobuf ../../test/run_layout.filter) # QUIET
fi

##############################################################################
set +x
echo "--- PNR: MAY SEG FAULT AFTER FLOORPLANNING"
echo "innovus -stylus -no_gui -abort_on_error -replay $wrapper"
cat $wrapper | sed 's/^/    /'
echo ""

set -x

# Use /sim/tmp because /tmp don't shake like that
export TMPDIR=/sim/tmp


FAIL=false
$nobuf innovus -stylus -no_gui -abort_on_error -replay $wrapper \
  |& ${filter[*]} \
  || FAIL=true

if [ "$FAIL" == true ]; then exit 13; fi

# Yeah we don't do this no more
# set +x
# if [ "$FAIL" == true ]; then
#   echo "--- PNR: RELOAD AND RETRY AFTER FLOORPLAN CRASH"
#   echo ""
#   echo "Oops looks like it failed, I was afraid of that."
#   echo "Reload floorplan and try again"
#   echo ""
#   # Note -stylus does verbose by default I think
#   set -x
#   ls -l     innovus.logv* || echo no logv
#   grep SEGV innovus.logv  || echo no SEGV
#   echo ""
#   echo ""
#   set -x
#   retry=../../scripts/top_flow_multi_vt_retry.tcl
#   $nobuf innovus -stylus -no_gui -abort_on_error -replay $retry \
#     |& ${filter[*]} \
#     || FAIL=true
#   set +x
#   ls -l innovus.logv* || echo no logv
# else
#   echo "--- PNR DID NOT CRASH? WHAT THE WHAT?"
# fi
# echo "DONE!"

# Wrapper lives in tmpdir
/bin/rm -rf $tmpdir

##############################################################################
set +x
echo "+++ PNR SUMMARY - "
echo ""
# synth_dir=.
synth_dir=$topdir/tapeout_16/synth/GarnetSOC_pad_frame
cd $synth_dir
  ls -l innovus.logv* || echo no logv
  echo ''
  echo 'grep ERROR innovus.log*'
  grep ERROR innovus.log* | grep -v logv | uniq
  echo ''
  echo 'grep "DRC violations"  innovus.logv* | tail -n 1'
  echo 'grep "Message Summary" innovus.logv* | tail -n 1'
  echo ""

  # grep "DRC violations"  innovus.logv* | tail -n 1
  # grep "Message Summary" innovus.logv* | tail -n 1

  for f in innovus.logv*; do  grep "DRC violations"  $f | tail -n 1; done
  for f in innovus.logv*; do  grep "Message Summary" $f | tail -n 1; done

  echo ""
  echo "CLOCK"
  pwd
  ls  pnr.clocks || echo no clocks
  cat pnr.clocks \
    | sed -n '/Descriptions/,$p' | sed -n '4,$p' || echo no clocks









# # (Most of this is copied from synth/README file in tapeout_sr)
# 
# # Copy in a full-chip post-synthesis netlist, see notes below
# % synth_src=$CACHEDIR/synth/
# % cp -rp $synth_src/GarnetSOC_pad_frame/ garnet/tapeout_16/synth
# 
# # Make your way to the new local synth dir
# % cd garnet/tapeout_16/synth/GarnetSOC_pad_frame/
