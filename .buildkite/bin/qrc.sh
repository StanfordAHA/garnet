#!/bin/bash

# Helper script for the process of running postroute_hold step ten
# times in a row to try and see how often QRC fails.
# 
# Designed to be called from a buildkite yml script something like:
# 
#     - label:    'qrc0'
#       commands: '.buildkite/bin/qrc.sh'
#     - wait:     { continue_on_failure: true }
#     
#     - label:    'qrc1'
#       commands: '.buildkite/bin/qrc.sh'
#     - wait:     { continue_on_failure: true }
# 
#     ...
#     
#     - label:    'qrc9'
#       commands: '.buildkite/bin/qrc.sh'
#     - wait:     { continue_on_failure: true }
# 
# Assumes a lot of assume-o's

# Cached design for postroute_hold inputs lives here
REF=/build/gold.228

# Results will go to dirs e.g. /build/qtry.3549-{0,1,2,3,4,5,6,7,8,9}
DESTDIR=/build/qtry.${BUILDKITE_BUILD_NUMBER}

for i in 0 1 2 3 4 5 6 7 8 9; do
    if ! test -e ${DESTDIR}-$i; then
        DESTDIR=${DESTDIR}-$i
        break
    fi
done

# Tee stdout to a log file
exec > >(tee -i make-qrc.log) || exit 13
exec 2>&1 || exit 13


source mflowgen/bin/setup-buildkite.sh --dir $DESTDIR --need_space 1G;
mflowgen run --design $GARNET_HOME/mflowgen/full_chip;

echo "--- QRC TEST RIG SETUP - copy/link cached info";
set -x;

    ln -s $REF/full_chip/12-tsmc16;
    ln -s $REF/full_chip/20-cadence-innovus-flowsetup;
    ln -s $REF/full_chip/28-cadence-innovus-postroute;

    step=cadence-innovus-postroute_hold;

    mkdir -p 29-${step}; cd 29-${step};

    d=$REF/full_chip/*-${step};

    # log dir
    mkdir -p logs; mkdir -p outputs

    # symlinks
    cp -rp $d/innovus-foundation-flow         . ;

    # plain files
    cp -p $d/mflowgen-check-postconditions.py . ;
    cp -p $d/mflowgen-check-preconditions.py  . ;
    cp -p $d/mflowgen-debug                   . ;
    cp -p $d/mflowgen-run                     . ;
    cp -p $d/configure.yml                    . ;
    cp -p $d/START.tcl                        . ;

    # dirs
    cp -rp $d/inputs  . ;
    cp -rp $d/scripts . ;
set +x;

echo "--- QRC TEST RIG SETUP - swap in new main.tcl";

########################################################################
# Build a new main.tcl

main_tcl_new='
setOptMode -verbose true

setOptMode -usefulSkewPostRoute true

setOptMode -holdTargetSlack  $::env(hold_target_slack)
setOptMode -setupTargetSlack $::env(setup_target_slack)

puts "Info: Using signoff engine = $::env(signoff_engine)"

if { $::env(signoff_engine) } {
  setExtractRCMode -engine postRoute -effortLevel signoff
}
# setExtractRCMode -engine postRoute -effortLevel high


echo "BEGIN SYSENV"
printenv
echo "END SYSENV"

# echo ""
# echo "--- BEGIN generateRCFactor"
# Hope setExtractRCMode is sufficient to handle all the parms
# generateRCFactor

echo ""
echo "--- BEGIN optDesign -postRoute -hold"
setDistributeHost -local
setMultiCpuUsage -localCpu 8

# Run the final postroute hold fixing
optDesign -postRoute -outDir reports -prefix postroute_hold -hold
'

########################################################################
# Write the new main.tcl

echo "$main_tcl_new" > scripts/main.tcl
echo '=================================================================='
echo 'cat scripts/main.tcl'
cat scripts/main.tcl
echo '=================================================================='



# DO IT MAN!
echo "--- restore-design and setup-session"; # set -o pipefail;
pwd
ls -l ./mflowgen-run
set -x
(
    set -x
    echo exit 13 | ./mflowgen-run && echo ENDSTATUS=PASS || echo ENDSTATUS=FAIL
) |& tee mflowgen-run.log
set +x

# (./mflowgen-run || echo ENDSTATUS=FAIL) >& mflowgen-run.log.1 &


# bug out if errors
echo "+++ ERRORS? And end-game"

set -x
egrep '^ Error messages' qrc*.log



grep ENDSTATUS mflowgen-run.log

grep ENDSTATUS=FAIL mflowgen-run.log && echo "FAILED endstatus, could initiate retry here"
grep ENDSTATUS=FAIL mflowgen-run.log && exit 13

n_errors=$(egrep '^ Error messages' mflowgen-run.log | awk '{print $NF}')
# e.g. n_errors='0\n0\n0\n0\n'
for i in $n_errors; do 
    # if [ "$n_errors" -gt 0 ]; then exit 13; fi
    if [ "$n_errors" -gt 0 ]; then 
        echo "FAILED n_errors, could initiate retry here"
        exit 13;
    fi
done

# Clean up
echo "--- save disk space, delete output design (?)"
set -x
ls -lR checkpoints/
/bin/rm -rf checkpoints/*
touch checkpoints/'deleted to save space'

exit



# THIS IS WHAT FAILED QRC LOOKS LIKE
# 
#  Tool:                    Cadence Quantus Extraction 64-bit
#  Version:                 19.1.1-s086 Mon Mar 25 09:39:10 PDT 2019
#  IR Build No:             086 
#  Techfile:                Unknown ; version: Unknown 
#  License(s) used:         0 of Unknown 
#  User Name:               buildkite-agent
#  Host Name:               r7arm-aha
#  Host OS Release:         Linux 3.10.0-862.11.6.el7.x86_64
#  Host OS Version:         #1 SMP Tue Aug 14 21:49:04 UTC 2018
#  Run duration:            00:00:00 CPU time, 00:01:19 clock time
#  Max (Total) memory used: 0 MB
#  Max (CPU) memory used:   0 MB
#  Max Temp-Directory used: 0 MB
#  Nets/hour:               0K nets/CPU-hr, 0K nets/clock-hr
#  Design data:
#     Components:           0
#     Phy components:       0
#     Nets:                 0
#     Unconnected pins:     0
#  Warning messages:        430
#  Error messages:          2






# ##############################################################################
# main_tcl_orig='''
# setOptMode -verbose true
# 
# setOptMode -usefulSkewPostRoute true
# 
# setOptMode -holdTargetSlack  $$::env(hold_target_slack)
# setOptMode -setupTargetSlack $$::env(setup_target_slack)
# 
# puts "Info: Using signoff engine = $$::env(signoff_engine)"
# 
# if { $$::env(signoff_engine) } {
#   setExtractRCMode -engine postRoute -effortLevel signoff
# }
# 
# # Run the final postroute hold fixing
# optDesign -postRoute -outDir reports -prefix postroute_hold -hold
# '''
# 
# ##############################################################################
# main_tcl_new='
# setOptMode -verbose true
# 
# setOptMode -usefulSkewPostRoute true
# 
# setOptMode -holdTargetSlack  $$::env(hold_target_slack)
# setOptMode -setupTargetSlack $$::env(setup_target_slack)
# 
# puts "Info: Using signoff engine = $$::env(signoff_engine)"
# 
# if { $$::env(signoff_engine) } {
#   setExtractRCMode -engine postRoute -effortLevel signoff
# }
# 
# # Hope setExtractRCMode is sufficient to handle all the parms
# generateRCFactor
# 
# 
# # Run the final postroute hold fixing
# # optDesign -postRoute -outDir reports -prefix postroute_hold -hold
# '
# 
# echo "$main_tcl_new"
