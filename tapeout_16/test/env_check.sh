#!/bin/bash

# **SOURCE** this file, don't try and execute it :(

function subheader {
  pfx=$1; shift
  echo "------------------------------------------------------------------------"
  echo "$*"
}

  ##############################################################################
  subheader +++ VERIFY PYTHON VERSION AND PACKAGES

  # Check for python3.7 FIXME I'm sure there's a better way... :(
  # ERROR: Package 'peak' requires a different Python: 3.6.8 not in '>=3.7' :(
  v=`python3 -c 'import sys; print(sys.version_info[0]*1000+sys.version_info[1])'`
  echo "Found python version $v -- should be at least 3007"
  if [ $v -lt 3007 ] ; then
    echo ""; echo "ERROR found python version $v -- should be 3007"; exit 13
  fi
  echo ""

  subheader +++ VERIFY PYTHON PACKAGE REQUIREMENTS
  ##############################################################################
  # Check requirements
  # From garnet README:
  #   Install python dependencies
  #   $ pip install -r requirements.txt  # install python dependencies
  if [ "$VERBOSE" == true ];
    then test/requirements_check.sh -v || exit 13
    else test/requirements_check.sh -q || exit 13
  fi
  echo ""


##############################################################################
# Need to know that innovus is not throwing errors!!!
subheader +++ VERIFYING CLEAN INNOVUS
echo ""; 
echo "innovus -no_gui -execute exit"
nobuf='stdbuf -oL -eL'
if [ "$VERBOSE" == "true" ] ; 
  then filter=($nobuf cat)
  else filter=($nobuf egrep 'Version|ERROR|Summary')
fi

# It leaves little turds, so use a temp directory
# (note "--- " has special meaning in kite logs...)
mkdir tmp.$$; cd tmp.$$
  $nobuf innovus -no_gui -execute exit |& $nobuf tee tmp.iout \
    | $nobuf sed 's/^--- /^=== /' \
    | ${filter[*]}
  grep ERROR tmp.iout > /dev/null && ierr=true || ierr=false
cd ..; /bin/rm -rf tmp.$$
if [ "$ierr" == "true" ] ; then
    echo ""
    echo "ERROR looks like innovus install is not clean!"
    exit 13
fi



