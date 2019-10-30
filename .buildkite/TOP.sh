#!/bin/bash

# Exit on error from any pipe stage of any command
set -eo pipefail

VERBOSE=false
if [ "$1" == "-v" ]; then VERBOSE=true;  shift; fi
if [ "$1" == "-q" ]; then VERBOSE=false; shift; fi

topdir=`pwd`

##############################################################################
# optDesign? NO OPTDESIGN!!!
# export VTO_OPTDESIGN=0
if [ "$VTO_OPTDESIGN" == "" ] ; then
    export VTO_OPTDESIGN=1
    echo "@file_info: Using default VTO_OPTDESIGN=$VTO_OPTDESIGN"
else
    echo "@file_info: Found existing env var VTO_OPTDESIGN=$VTO_OPTDESIGN"
fi
echo "@file_info: VTO_OPTDESIGN=$VTO_OPTDESIGN"

##############################################################################
# PROCESS COMMAND LINE ARGUMENTS

if [ "$1" == "--help" ] ; then
  echo "Example:"
  echo "  $0 floorplan place cts fillers route opt eco"
  echo "  $0 all"
  echo ""
  exit 13
fi

if [ $# -gt 0 ] ; then
    # E.g. "-fill -plan" => "fill plan"
    export VTO_STAGES=`echo $* | sed 's/-//g'`
fi

# DEFAULT
# export VTO_STAGES="floorplan place cts fillers route opt eco"
if [ "$VTO_STAGES" == "" ] ; then
    export VTO_STAGES="all"
    echo "@file_info: Using default VTO_STAGES='$VTO_STAGES'"
fi

echo "$0 will execute stages '$VTO_STAGES'"
echo ""

##############################################################################
# STAGES - now set by command line (above)
# 
# Everything (six stages)
# export VTO_STAGES="floorplan place cts fillers route eco"
# 
# gpf8 did this ish
# export VTO_STAGES="route eco"
# 
# For icovl experiments try skipping floorplan ONLY
# export VTO_STAGES="place cts fillers route eco"
# 
# Ready to start w/routing for our icovl/congestion experiments
# Actually have to start w/fill b/c error in prev run
# export VTO_STAGES="fillers route eco"
# 
# More errors but now at least I think we're ready for to begin w/route.
# export VTO_STAGES="route eco"
##############################################################################


########################################################################
echo "--- MODULE LOAD REQUIREMENTS"
echo ""
set +x; source tapeout_16/test/module_loads.sh


##############################################################################
echo "--- GENESIS2 GENERATES PAD FRAME I GUESS"
# 
# # using hack now instead, see below
# cd $topdir/pad_frame
#   # ./create_pad_frame.sh; 
#   Genesis2.pl -parse -generate -top   Garnet_SoC_pad_frame \
#                                -input Garnet_SoC_pad_frame.svp
echo "+++ HACK ALERT"
echo "- instead of auto-generating the io_file, as we should..."
echo "  we currently use a custom-built cached version found in Nikhil's directory"
echo "  stored locally as 'garnet/pad_frame/io_file_custom'; also see floorplan.tcl"
echo ""
# 
# # 9/25 hack eliminated a bunch of errors, see <issue>; keep the hack for now anyway
# set +x  # no echo commands
# echo "+++ HACK ALERT"
# echo "- generated pad_frame/io_file is WRONG I think (why?)"
# echo "- subbing in cached io_file from to_nikhil directory..."
# echo "cp /sim/ajcars/to_nikhil/updated_scripts/io_file ."
# test -e io_file && mv io_file io_file_orig
# cp /sim/ajcars/to_nikhil/updated_scripts/io_file .



########################################################################
# FETCH SYNTH COLLATERAL FROM PRIOR BUILD STAGES
# Yeah no pretty sure we do this locally too.
# if [ "$BUILDKITE" ]; then

  # Copy in the latest synth info from previous buildkite passes (PE, mem synth)
  # Copy cached collateral from synthesis step

  # CACHEDIR is set in pipeline.yml file, e.g.
  # env:
  #   CACHEDIR: /sim/buildkite-agent/builds/cache

  echo "--- FETCH SYNTH COLLATERAL FROM PRIOR BUILD STAGES"
  set -x
  cd $topdir/tapeout_16
  test -d synth || mkdir synth
  cd synth
  for f in append.csh PE/ run_all.csh Tile_MemCore/ Tile_PE/; do
    test -e $f && echo $f exists || echo $f not exists
    test -e $f || echo "cp -rp $CACHEDIR/synth/$f ."
    test -e $f ||       cp -rp $CACHEDIR/synth/$f .
  done

# fi








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



# ##############################################################################
# echo "--- FETCH SYNTH COLLATERAL FROM ALEX DIR (?)"
# set -x
# cd $topdir/tapeout_16
# synth_src=/sim/ajcars/aha-arm-soc-june-2019/implementation/synthesis/synth
# cp -rp $synth_src/GarnetSOC_pad_frame/ synth/


# # Using our own stuff now (I think)
# # a thing to try, instead of copying the whole dir
# ##############################################################################
# echo "--- LINK TO SYNTH COLLATERAL IN ALEX DIR (?)"
# set -x
# cd $topdir/tapeout_16/synth
# synth_src=/sim/ajcars/aha-arm-soc-june-2019/implementation/synthesis/synth
# # cp -rp $synth_src/GarnetSOC_pad_frame/ synth/
# test -d GarnetSOC_pad_frame || mkdir GarnetSOC_pad_frame
# cd GarnetSOC_pad_frame
# test -e results_syn || ln -s $synth_src/GarnetSOC_pad_frame/results_syn/






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

# if [ "$BUILDKITE" ]; then
#     mkdir $topdir/tapeout_16/synth/GarnetSOC_pad_frame
# fi

test -d  $topdir/tapeout_16/synth/GarnetSOC_pad_frame \
|| mkdir $topdir/tapeout_16/synth/GarnetSOC_pad_frame

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

# wrapper=../../scripts/top_garnet_redo.tcl
# 
# Trying a new thing
wrapper=../../scripts/top_garnet_staged.tcl

# PWR_AWARE=1
nobuf='stdbuf -oL -eL'

# innovus -stylus -no_gui -abort_on_error -replay $wrapper || exit 13

if [ "$VERBOSE" == true ];
  then filter=($nobuf cat)                          # VERBOSE
  else filter=($nobuf ../../test/run_layout.filter) # QUIET
fi

##############################################################################
set +x
# echo "--- PNR: MAY SEG FAULT AFTER FLOORPLANNING"
echo "--- PNR"
echo "innovus -stylus -no_gui -abort_on_error -replay $wrapper"
# cat $wrapper | sed 's/^/    /'
# echo ""

set -x

# Use /sim/tmp because /tmp don't shake like that
export TMPDIR=/sim/tmp

# Take out the traaaaash before running innovus
if [ "$BUILDKITE" ]; then
  ls -l innovus.{cmd,log}* || echo no trash
  rm    innovus.{cmd,log}* || echo no trash
fi

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
  ls -l innovus.log* || echo no logs
  echo ''
  echo 'grep ERROR innovus.log'
  # In the interest of brevity, excluve logv file matches
  egrep '^[^#]*\*ERR' innovus.log* | grep -v logv | uniq || echo No errors found
  echo ''
  echo 'grep "DRC violations"  innovus.logv* | tail -n 1'
  echo 'grep "Message Summary" innovus.logv* | tail -n 1'
  echo ""

  # grep "DRC violations"  innovus.logv* | tail -n 1
  # grep "Message Summary" innovus.logv* | tail -n 1

  (for f in innovus.logv*; do grep "DRC violations"  $f | tail -n 1; done)\
  || echo "No DRC violations"

  (for f in innovus.logv*; do grep "Message Summary" $f | tail -n 1; done)\
  || echo "No message summary(!)"


  echo ""
  echo "CLOCK"
  pwd
  if test -e pnr.clocks; then
    cat pnr.clocks \
      | sed -n '/Descriptions/,$p' | sed -n '4,$p' \
      || echo 'No clocks in pnr.clock report (?)'
  else
    echo 'no clocks (yet)'
  fi




# # (Most of this is copied from synth/README file in tapeout_sr)
# 
# # Copy in a full-chip post-synthesis netlist, see notes below
# % synth_src=$CACHEDIR/synth/
# % cp -rp $synth_src/GarnetSOC_pad_frame/ garnet/tapeout_16/synth
# 
# # Make your way to the new local synth dir
# % cd garnet/tapeout_16/synth/GarnetSOC_pad_frame/
