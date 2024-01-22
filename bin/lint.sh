#!/bin/bash

function which() { type $*; }
# which activate
# exit



# LOCAL_TEST=
# LOCAL_TEST=True

# Gather the python files
# [ "$LOCAL_TEST" ] && cd /nobackup/steveri/github/garnet
# files=`git ls-tree -r HEAD --name-only | egrep 'py$' | sort`

# set -x
# Fire up a venv if needed
if [ `hostname` == kiwi ]; then
  cd /nobackup/steveri/github/garnet
  # python -c 'import sys; print(sys.prefix)' ?? returns "/nobackup/steveri/github/smart-components/env"
  which activate || source /nobackup/steveri/github/smart-components/env/bin/activate
else
  cd /aha/garnet
fi

# Gather the python files
files=`git ls-tree -r HEAD --name-only | egrep 'py$' | sort`
echo $files


########################################################################
# AUTOFLAKE

DO_AF=True
if [ "$DO_AF" == True ]; then

    echo '--- Autoflake finds redundant and unnecessary import requests'

    # Install if needed
    echo '--- - AUTOFLAKE INSTALL'
    which autoflake >& /dev/null || pip install autoflake

    # Prevent unwanted logfile escape sequences
    filter='s/^---/ ---/;s/^+++/ +++/'

    echo '--- - AUTOFLAKE ERRORS'
    AF_FAIL=True
    autoflake --remove-duplicate-keys $files | sed "$filter" | grep . || AF_FAIL=

    # autoflake --remove-duplicate-keys codegen/io_placement.py
fi

########################################################################
# FLAKE8

DO_F8err=True
if [ "$DO_F8err" == True ]; then

    echo '--- Flake8 finds python style violations'

    # Install if needed
    echo '--- - FLAKE8 INSTALL'
    which flake8 >& /dev/null || pip install flake8

    # ERRORS
    echo '--- - FLAKE8 ERRORS'

    awkscript='
      { got_input=1 }
      fname != $1 { print "" }
      { print; fname = $1 }
      END { if (got_input) exit(13) }
    '
    function filter() { awk -F ':' "$awkscript"; }

    # Test (garnet.py only)
    # echo '------------------------------------------------------------------------'
    # F8_FAIL=False
    # flake8 --select=F garnet.py | filter || F8_FAIL=True
    # [ "$F8_FAIL" == True ] && echo FAILED
    # echo '------------------------------------------------------------------------'

    # Note it is MUCH faster to do files all at once vs. in a for loop
    F8_FAIL=False
    flake8 --select=F $files | filter || F8_FAIL=True
    [ "$F8_FAIL" == True ] && echo FAILED
fi

# WARNINGS

echo '--- - FLAKE8 WARNINGS'
cat <<EOF

NOTE to address warnings locally, do e.g.

    pip install flake8
    flake8 <filename>.py
  
EOF
awkscript='
    # { print }
    { n[$1]++ }
    prev_fname != $1 { if (NR-1) {
      printf("Found %4d warnings in file %s\n", n[prev_fname], prev_fname)
    }}
    { prev_fname = $1 }
    # fname != $1 { print "" }
    #    { print; fname = $1 }
    # END { if (got_input) exit(13) }
'
flake8 $files | awk -F ":" "$awkscript" | sort -b -k2,2rn

########################################################################
# Process failures
echo "+++ SUMMARY"
FAIL=

if [ "$AF_FAIL" ]; then
    FAIL=True
    cat <<EOF

----------------------------------------------------
ERROR: Found autoflake errors, see above for details.
To run autoflake locally do e.g.
    pip install autoflake
    autoflake --remove-duplicate-keys <filename>.py
EOF
fi    

if [ "$F8_FAIL" ]; then
    FAIL=True
    cat <<EOF

----------------------------------------------------
ERROR: Found flake8 errors, see above for details.
To run flake8 locally do e.g.
    pip install flake8
    flake8 --select=F <filename>.py
    flake8 <filename>.py

EOF
fi    


cat <<EOF

----------------------------------------------------
NOTE: To skip flake tests for a given python line,
can add '# noqa' at the end, e.g.
```
    if name == "main": garnet_amber.main()   # noqa
```
EOF


if [ "$FAIL" ]; then
    exit 13
else
    echo "No errors found, hooray!"
fi
