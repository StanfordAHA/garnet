#!/bin/bash
cp $GARNET_HOME/global_buffer/Makefile ./
cp -r $GARNET_HOME/global_buffer/testvectors ./
mkdir sim
cp -r $GARNET_HOME/global_buffer/sim/dump*.tcl ./sim/

if [ $tool = "XCELIUM" ]; then
  ln -s ./inputs/xcelium.d
elif [ $tool = "VCS" ]; then
  ln -s ./inputs/simv
  ln -s ./inputs/simv.daidir
fi


if [ $waveform = "True" ]; then
  WAVEFORM=1
else
  WAVEFORM=0
fi

for test in $(echo $rtl_testvectors | sed "s/,/ /g")
do
    set -x;
    RUN_LOG=${test}.log \
    RUN_ARGS=+${test} \
    WAVEFORM=$WAVEFORM \
    SAIF=0 \
    TOOL=$tool \
    make run;
    cat ${test}.log >> outputs/run.log;
done

cd outputs

if [ $waveform = "True" ]; then
  if [ $tool = "XCELIUM" ]; then
    ln -s ../global_buffer.shm global_buffer.shm
  elif [ $tool = "VCS" ]; then
    ln -s ../global_buffer.fsdb global_buffer.fsdb
  fi
fi

