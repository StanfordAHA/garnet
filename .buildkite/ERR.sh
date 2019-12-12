#!/bin/bash

# Nice readable summary of all errors for a given buildkite run.

# ls -1 /tmp/*398*
# /tmp/errors-top-398-PNR1(plan).txt
# /tmp/errors-top-398-PNR2(place).txt
# /tmp/errors-top-398-PNR3(cts).txt
# /tmp/errors-top-398-PNR4(fill).txt
# /tmp/errors-top-398-PNR5(route).txt
# /tmp/errors-top-398-PNR6(opt).txt
# /tmp/errors-top-398-PNR7(eco).txt

if [ ! "$BUILDKITE_BUILD_NUMBER" ]; then
   echo "No env var BUILDKITE_BUILD_NUMBER => test mode"
   BUILDKITE_BUILD_NUMBER=398
   fnroot=/tmp/errors-top-$BUILDKITE_BUILD_NUMBER
   ls -1 ${fnroot}* | sed 's/^/  /'
   echo ""
fi
fnroot=/tmp/errors-top-$BUILDKITE_BUILD_NUMBER

drc_problems='False'
for f in ${fnroot}*; do
    # E.g. label="PNR1(plan)
    label=`echo $f | sed 's/.*\(PNR.*\).txt/\1/'`
    # echo -n label=$label

    n_errors=`grep \*ERROR $f | wc -l`
    # echo -n , n_errors=$n_errors

    n_drc=`grep 'DRC violations =' $f | awk '{print $NF}'`
    if [ "$n_drc" == "" ]; then n_drc=0; fi
    # echo -n , n_drc=$n_drc
    if [ "$n_drc" > 0 ]; then drc_problems="True"; fi

    # *** Message Summary: 3019 warning(s), 15 error(s)
    msum=`grep '* Message Summary' $f | sed 's/.*Summary: //'`
    # echo -n ", msum='$msum'"; echo ""

    # echo $label $n_errors $n_drc
    # Don't need $n_errors, it's redundant w/ message summary. Want:

    # PNR1(plan)___0_DRC_violations__2455106_warning(s),__0_error(s)
    # PNR2(place)__0_DRC_violations___319462_warning(s),__0_error(s)
    # PNR3(cts)____0_DRC_violations___970193_warning(s),__1_error(s)
    # PNR4(fill)___0_DRC_violations___967612_warning(s),__0_error(s)
    # PNR5(route)_33_DRC_violations_____3019_warning(s),__0_error(s)
    # PNR6(opt)____0_DRC_violations_____3504_warning(s),__2_error(s)
    # PNR7(eco)___40_DRC_violations____18149_warning(s),__0 error(s)

    # echo $label $n_drc \
    #     | awk '{printf("--- %-12s %2d DRC violations -- ", $1, $2)}'
    # echo $msum
    echo $label $n_drc "$msum" \
        | awk '{printf("%-12s %2d DRC violations   %7d warnings  %2d errors\n", $1, $2, $4, $6)}'\
        | sed 's/ /_/g' | sed 's/^/--- /'

    grep \*ERROR $f
    echo ""
done

# echo '+++ TEST PLEEASE IGNORE:'
# echo '+++ "test1(dq)  33 DRC violations --   3019 warning(s),  0 error(s)"'
# echo "+++ 'test2(sq) 444 DRC violations -- 66,666 warning(s), 12 error(s)'"

if [ "$drc_problems" == "True" ]; then exit 13; fi


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

