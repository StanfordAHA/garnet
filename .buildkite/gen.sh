#!/bin/bash

# Exit on error in any stage of any pipeline
set -eo pipefail

VERBOSE=false
if   [ "$1" == "-v" ] ; then VERBOSE=true;  shift;
elif [ "$1" == "-q" ] ; then VERBOSE=false; shift;
fi

##############################################################################
echo "--- SETUP AND VERIFY ENVIRONMENT"
# (Probably could/should skip this step for buildkite)
#   - set -x; cd tapeout_16; set +x; source test/module_loads.sh; set -x

set +x
source .buildkite/setup.sh
set -x

set +x
  if [ "$VERBOSE" == true ];
    then bin/requirements_check.sh -v
    else bin/requirements_check.sh -q
  fi

echo ""

export PATH=/usr/local/bin:$PATH

echo "--- GEN RTL"
cd tapeout_16
./gen_rtl.sh
ls ../genesis_verif
cd ../

set -x
