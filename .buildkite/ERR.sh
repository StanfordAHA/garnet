#!/bin/bash

# Nice readable summary of all errors for a given buildkite run.

# ls -1 /tmp/TOP-errors/398
# /tmp/TOP_errors/398/PNR1(plan).txt
# /tmp/TOP_errors/398/PNR2(place).txt
# /tmp/TOP_errors/398/PNR3(cts).txt
# /tmp/TOP_errors/398/PNR4(fill).txt
# /tmp/TOP_errors/398/PNR5(route).txt
# /tmp/TOP_errors/398/PNR6(opt).txt
# /tmp/TOP_errors/398/PNR7(eco).txt

# Test mode, test bk number should be on command line
# e.g. 'ERR.sh 434' to test /tmp/TOP-errors/434/PNR* file(s)
if [ ! "$BUILDKITE_BUILD_NUMBER" ]; then
   echo "No env var BUILDKITE_BUILD_NUMBER => test mode"
   BUILDKITE_BUILD_NUMBER=$1
   echo "Will test /tmp/TOP-errors/$BUILDKITE_BUILD_NUMBER/PNR*"
   echo ""
fi
errdir=/tmp/TOP-errors/$BUILDKITE_BUILD_NUMBER
if ! test -d $errdir; then
    echo "ERROR cannot find err dir '$errdir'"
    exit 13
fi

drc_problems='False'
for f in ${errdir}/*; do
    n_drc=`grep 'DRC violations =' $f | awk '{print $NF}'`
    if [ "$n_drc" == "" ]; then n_drc=0; fi
    if [ "$n_drc" >  0  ]; then drc_problems="True"; fi

    # Want:
    # PNR1(plan)___0_DRC_violations__2455106_warning(s),__0_error(s)
    # PNR2(place)__0_DRC_violations___319462_warning(s),__0_error(s)
    # PNR3(cts)____0_DRC_violations___970193_warning(s),__1_error(s)
    # PNR4(fill)___0_DRC_violations___967612_warning(s),__0_error(s)
    # PNR5(route)_33_DRC_violations_____3019_warning(s),__0_error(s)
    # PNR6(opt)____0_DRC_violations_____3504_warning(s),__2_error(s)
    # PNR7(eco)___40_DRC_violations____18149_warning(s),__0 error(s)

    # *** Message Summary: 3019 warning(s), 15 error(s)
    msum=`grep '* Message Summary' $f | sed 's/.*Summary: //'`

    # E.g. label="PNR1(plan)
    # echo -n label=$label
    label=$(basename $f) ; # /foo/bar/baz.txt => baz.txt
    label="${label%.*}"  ; #          baz.txt => baz
    echo $label $n_drc "$msum" \
        | awk '{printf("%-12s %2d DRC violations   %7d warnings  %2d errors\n", $1, $2, $4, $6)}'\
        | sed 's/ /_/g' | sed 's/^/--- /' > /tmp/tmp$$

    # OOPS sometimes log reports no errors but there are ERRORS anyway
    n_ERRORS=`grep \*ERROR $f | wc -l`
    echo `cat /tmp/tmp$$` " ...and/or including $n_ERRORS ERROR(s)"
    grep \*ERROR $f
    /bin/rm /tmp/tmp$$
    echo ""
done

########################################################################
echo "+++ FINAL CHECK"
echo ""
if [ "$drc_problems" == "True" ]; then
    echo "Problems were found (see above) but may not have been fatal"
fi
########################################################################
# The only thing that matters is the final final drc check.  Result of
# final check should be in file '/tmp/errors-top-434-PNR6(opt).txt'
# It should look something like this:
#     @file_info FINAL ERROR COUNT: 5 error(s)
# 
final_stage=`/bin/ls ${errdir}/PNR7*`
echo Checking $final_stage for final error count...
final_error_count=`\
  grep 'FINAL ERROR COUNT' $final_stage \
  | tail -n 1 | awk '{print $5}'
`
if [ "$final_error_count" == "" ]; then
    echo OOPS final error count not found
    exit 13
fi
echo ""
echo '----------------------------------------'
# echo "grep 'FINAL ERROR COUNT' $final_stage"
grep 'FINAL ERROR COUNT' $final_stage | tail -1
echo '----------------------------------------'
if [ "$final_error_count" == 0 ]; then
    exit 0
else
    exit 13
fi



########################################################################

# [12/05 01:36:46  40811s] #Total number of DRC violations = 5460
# [12/05 01:45:07  41478s] *** Message Summary: 3019 warning(s), 15 error(s)
# 
# 
#   **ERROR: (IMPFP-3356):        IO Inst ANAIOPAD_AVDD is outside of design boundary. All placed IO instances must be located insid
# e the design boundary. Move IO instance to a location within the design boundary.
# 
# +++ grep "DRC violations"  innovus.logv* | tail -n 1
# +++ grep "Message Summary" innovus.logv* | tail -n 1
# 
# [12/05 01:36:46  40811s] #Total number of DRC violations = 5460
# [12/05 01:45:07  41478s] *** Message Summary: 3019 warning(s), 15 error(s)
# 
# 
# +++ PNR6(opt)
# /sim/buildkite-agent/builds/bigjobs-2/tapeout-aha/top/tapeout_16/synth/GarnetSOC_pad_frame
# 
# --- grep ERROR innovus.log
#   **ERROR: (IMPFP-3356):        IO Inst IOPAD_top_VDD_dom3 is outside of design boundary. All placed IO instances must be located 
# inside the design boundary. Move IO instance to a location within the design boundary.

    # echo $label $n_drc \
    #     | awk '{printf("--- %-12s %2d DRC violations -- ", $1, $2)}'
    # echo $msum

# echo '+++ TEST PLEEASE IGNORE:'
# echo '+++ "test1(dq)  33 DRC violations --   3019 warning(s),  0 error(s)"'
# echo "+++ 'test2(sq) 444 DRC violations -- 66,666 warning(s), 12 error(s)'"

