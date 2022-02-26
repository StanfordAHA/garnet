#!/bin/bash
ln -s ./inputs/Makefile
ln -s ./inputs/sim
ln -s ./inputs/testvectors

if [ $waveform = "True" ]; then
    WAVEFORM=1
else
    WAVEFORM=0
fi

if [ $saif = "True" ]; then
    SAIF=1
else
    SAIF=0
fi

if [ $tool = "XCELIUM" ]; then
    ln -s ./inputs/xcelium.d
elif [ $tool = "VCS" ]; then
    ln -s ./inputs/simv
    ln -s ./inputs/simv.daidir
fi

(
    set -x;
    RUN_LOG=${test}.log \
    RUN_ARGS=+${test} \
    WAVEFORM=$WAVEFORM \
    SAIF=${SAIF} \
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
        ln -s ../global_buffer.fsdb run.fsdb
    fi
fi

# Quick fix because synopsys requires backslash as an escape key for bracket
cd ..
if [ $saif = "True" ]; then
    if [ $tool = "XCELIUM" ]; then
        sed -i 's/\[\([^]\\]*\)\]/\\\[\1\\\]/g' *.saif
    fi
fi
