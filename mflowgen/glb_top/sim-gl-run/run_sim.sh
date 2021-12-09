#!/bin/bash
cp $GARNET_HOME/global_buffer/Makefile ./
cp -r $GARNET_HOME/global_buffer/testvectors ./
mkdir sim
cp -r $GARNET_HOME/global_buffer/sim/dump*.tcl ./sim/

if [ $waveform = "True" ]; then
    WAVEFORM=1
else
    WAVEFORM=0
fi

if [ $tool = "XCELIUM" ]; then
    ln -s ./inputs/xcelium.d
elif [ $tool = "VCS" ]; then
    ln -s ./inputs/simv
    ln -s ./inputs/simv.daidir
fi

# for test in $(echo $testvectors | sed "s/,/ /g")
# do
#     set -x;
#     RUN_LOG=${test}.log \
#     RUN_ARGS=+TEST=${test} \
#     WAVEFORM=$WAVEFORM \
#     SAIF=${saif} \
#     TOOL=$tool \
#     make run;
#     cat ${test}.log >> outputs/run.log;
#     if [ $saif = "True" ]; then
#         mv run.saif ${test}.saif;
#     fi
# done
# cd outputs
# 
# for test in $(echo $testvectors | sed "s/,/ /g")
# do
#     if [ $saif = "True" ]; then
#         ln -s ../${test}.saif
#     fi
# done

(
    set -x;
    RUN_LOG=${test}.log \
    RUN_ARGS=+${test} \
    WAVEFORM=$WAVEFORM \
    SAIF=${saif} \
    TOOL=$tool \
    make run;
    cat ${test}.log >> outputs/run.log;
)
cd outputs
if [ $saif = "True" ]; then
  ln -s ../run.saif
fi

if [ $waveform = "True" ]; then
    if [ $tool = "XCELIUM" ]; then
        ln -s ../global_buffer.shm global_buffer.shm
    elif [ $tool = "VCS" ]; then
        ln -s ../global_buffer.fsdb global_buffer.fsdb
    fi
fi

# Quick fix because synopsys requires backslash as an escape key for bracket
cd ..
if [ $saif = "True" ]; then
    if [ $tool = "XCELIUM" ]; then
        sed -i 's/\[\([^]\\]*\)\]/\\\[\1\\\]/g' *.saif
    fi
fi
