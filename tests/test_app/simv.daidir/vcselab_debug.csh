#!/bin/csh -f

cd /aha/garnet/tests/test_app

#This ENV is used to avoid overriding current script in next vcselab run 
setenv SNPS_VCSELAB_SCRIPT_NO_OVERRIDE  1

/cad/synopsys/vcs/S-2021.09-SP1/linux64/bin/vcselab $* \
    -o \
    simv \
    -nobanner \
    +vcs+lic+wait \

cd -

