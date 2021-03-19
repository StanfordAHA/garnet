#!/bin/bash

# Assumes a lot of assume-o's

REF=/build/gold.228;
GOLD=/build/qrc.${BUILDKITE_BUILD_NUMBER};
source mflowgen/bin/setup-buildkite.sh --dir $GOLD --need_space 1G;
mflowgen run --design $GARNET_HOME/mflowgen/full_chip;

echo "--- SETUP";
set -x;

    ln -s $REF/full_chip/12-tsmc16;
    ln -s $REF/full_chip/20-cadence-innovus-flowsetup;
    ln -s $REF/full_chip/28-cadence-innovus-postroute;

    step=cadence-innovus-postroute_hold;

    mkdir -p 29-${step}; cd 29-${step};

    d=$REF/full_chip/*-${step};

    # log dir
    mkdir -p logs;

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

# DO IT MAN!
echo "--- MAKE PRHOLD"; set -o pipefail;
echo exit 13 | mflowgen-run |& tee mflowgen-run.log;
