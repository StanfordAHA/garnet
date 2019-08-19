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

##############################################################################
# Check requirements
# From garnet README:
#   Install python dependencies
#   $ pip install -r requirements.txt  # install python dependencies

function check_pip {
  # echo "Verifying existence of python package '$1'..."
  pkg="$1"; pkg_found=true
  found=`pip3 list | awk '$1=="'$pkg'"{ print "found"}'`
  if [ $found ] ; then 
    [ $VERBOSE == true ] && echo "  Found package '$pkg'"
    return 0
  else
    echo "  ERROR Cannot find installed python package '$pkg'"
    exit 13
  fi
}

packages=`cat ../requirements.txt \
    | sed 's/.*egg=//' \
    | sed 's/==.*//' \
    | sed 's/buffer_mapping/buffer-mapping/' \
    | sed 's/ordered_set/ordered-set/' \
    | sed 's/cosa/CoSA/' \
    | awk '{print $1}'
  `
echo Need python packages $packages
found_missing=false
for pkg in $packages; do
  (check_pip $pkg) || found_missing=true
done
if [ $found_missing == true ]; then
  echo ""
  echo "ERROR missing packages, maybe need to do pip3 install -r ../requirements.txt"
  exit 13
fi
echo Found all packages
