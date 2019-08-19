#!/bin/bash

VERBOSE=false
if [ "$1" == "-v" ]; then VERBOSE=true; fi

expr `pwd` : '.*/tapeout_16$' > /dev/null && rightplace=true || rightplace=false
if [ $rightplace != true ] ; then
  echo ""
  echo "ERROR looks like you're in the wrong place"
  echo "- you are here:   `pwd`"
  echo "- should be here: .../tapeout_16"
  exit 13
fi

# For "module load" requirements see README, alex .cshrc
# FIXME consider a "requirements.txt" for module load's

# echo HOME=$HOME    # HOME=/var/lib/buildkite-agent
# echo USER=$USER    # USER=buildkite-agent

# To forestall warning : '/home/steveri/.modules' not found
# +(0):WARN:0: Directory '/var/lib/buildkite-agent/.modules' not found
test -f $HOME/.modules || rm    $HOME/.modules # fix your wagon!
test -d $HOME/.modules || mkdir $HOME/.modules

set +x # no echo sourced crap
source /cad/modules/tcl/init/bash

module load base
module load genesis2
module load incisive/15.20.022
module load lc
module load syn/latest

# Note alternative for genesis2 load is keyi's possibly-more-reliable
# "pip install genesis2"

# Weird innovus v. genus dependence...
echo "
#
# NOTE `module load genus` loads innovus v17 as a side effect.
# So to get the correct innovus v19, 
# `module load innovus/19.10.000` must happen *after* `module load genus`.
#
"
set -x; /usr/bin/which innovus; /usr/bin/which genus; set +x
echo module load genus;             module load genus
echo module load innovus/19.10.000; module load innovus/19.10.000
set -x; /usr/bin/which innovus; /usr/bin/which genus; set +x
# Should be
#   /cad/cadence/GENUS17.21.000.lnx86/bin/genus
#   /cad/cadence/INNOVUS19.10.000.lnx86/bin/innovus

version_found=`/usr/bin/which innovus`
version_wanted="/cad/cadence/INNOVUS19.10.000.lnx86/bin/innovus"
if [ $version_found != $version_wanted ] ; then
    echo ""
    echo "ERROR innovus version changed"
    echo "- found  '$version_found'"
    echo "- wanted '$version_wanted'"
    exit 13
fi
version_found=`/usr/bin/which genus`
version_wanted="/cad/cadence/GENUS17.21.000.lnx86/bin/genus"
if [ $version_found != $version_wanted ] ; then
    echo ""
    echo "ERROR genus version changed"
    echo "- found  '$version_found'"
    echo "- wanted '$version_wanted'"
    exit 13
fi
