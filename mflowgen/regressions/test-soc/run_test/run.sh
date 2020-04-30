#!/usr/bin/env bash

CXDT=`readlink -f inputs/CXDT.bin`
SIMV=`readlink -f inputs/simv`
SIMV_DAIDIR=`readlink -f inputs/simv.daidir`

MAX_SIM_TIME="60000us"

ln -s ${CXDT} CXDT.bin
ln -s ${SIMV} simv
ln -s ${SIMV_DAIDIR} simv.daidir

echo "quit" > quit.do
touch image.hex

./simv +vcs+lic+wait +vcs+flush+log +vcs+finish+${MAX_SIM_TIME} -assert nopostproc < quit.do | tee outputs/vcs_run_${TEST_NAME}.log
