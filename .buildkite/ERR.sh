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

for f in ${fnroot}*; do
    # E.g. label="PNR1(plan)
    label=`echo $f | sed 's/.*\(PNR.*\).txt/\1/'`
    # echo -n label=$label

    n_errors=`grep \*ERROR $f | wc -l`
    # echo -n , n_errors=$n_errors

    n_drc=`grep 'DRC violations =' $f | awk '{print $NF}'`
    if [ "$n_drc" == "" ]; then n_drc=0; fi
    # echo -n , n_drc=$n_drc

    # *** Message Summary: 3019 warning(s), 15 error(s)
    msum=`grep '* Message Summary' $f | sed 's/.*Summary: //'`
    # echo -n ", msum='$msum'"; echo ""

    # echo $label $n_errors $n_drc

    # Don't need $n_errors, it's redundant w/ message summary
    # echo $label $n_drc $n_errors \
    #     | awk '{printf("+++ %-12s %d DRC violations, %d errors -- ", $1, $2, $3)}';\

    echo $label $n_drc \
        | awk '{printf("+++ %-12s %d DRC violations -- ", $1, $2)}';\

    echo $msum
    grep \*ERROR $f
    echo ""

    

done


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

