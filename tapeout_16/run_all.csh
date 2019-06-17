#! /bin/tcsh
# Takes in top level design name as argument and
# # runs basic synthesis script
setenv DESIGN $1
setenv PWR_AWARE $2
if ("$3" == "") then 
    setenv TOP ""
else
    setenv TOP "TOP"
endif
# Start of synthesis
./run_synthesis.csh ${DESIGN} ${PWR_AWARE} ${TOP}
# Start of pnr
./run_layout.csh ${DESIGN} ${PWR_AWARE}
# Start of ncsim test
source ../../scripts/run_ncsim_${1}.csh > NCSIM.LOG
cd ../..
