#!/bin/bash

# Fire up a venv if running locally on kiwi
if [ `hostname` == kiwi ]; then
  cd /nobackup/steveri/github/garnet
  # python -c 'import sys; print(sys.prefix)' ?? returns ".../smart-components/env"
  type activate >& /dev/null ||     # "type" fails if activate not in path
      source /nobackup/steveri/github/smart-components/env/bin/activate
else
  cd /aha/garnet
fi

# Gather the python files
files=`git ls-tree -r HEAD --name-only | egrep 'py$' | sort`
echo $files


########################################################################
# AUTOFLAKE

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

# Install if needed
echo '--- Flake8 finds style problems in python files'
echo '--- - FLAKE8 INSTALL'
type flake8 >& /dev/null || pip install flake8

# filter function formats flake8 output for nice log display
awkscript='
    { got_input=1 }
    fname != $1 { print "" }
    { print; fname = $1 }
    END { if (got_input) exit(13) }
'
function filter() { awk -F ':' "$awkscript"; }


########################################################################
# FLAKE8 "E" PEP8 ERRORS

    echo '--- - FLAKE8 "E" PEP8 ERRORS'
    flake8 --select=E $files | filter && EFAIL= || EFAIL=True
    if [ "$EFAIL" ]; then
        EFAIL=`flake8 --select=E $files | wc -l`
        printf "%s ...........................Found %6d %s errors\n" --- $EFAIL E
    fi

########################################################################
# FLAKE8 "F" FLAKE ERRORS

    echo '--- - FLAKE8 "F" FLAKE ERRORS'
    flake8 --select=F $files | filter && FFAIL= || FFAIL=True
    if [ "$FFAIL" ]; then
        FFAIL=`flake8 --select=F $files | wc -l`
        printf "%s ...........................Found %6d %s errors\n" --- $FFAIL F
    fi

########################################################################
# FLAKE8 "W" PEP8 WARNINGS

echo '--- - FLAKE8 "W" PEP8 WARNINGS'
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
flake8 --select=W $files | awk -F ":" "$awkscript" | sort -b -k2,2rn

########################################################################
# Process failures
echo "+++ SUMMARY"
FAIL=

########################################################################
if [ "$AF_FAIL" ]; then FAIL=True; cat <<EOF

----------------------------------------------------
ERROR: Found autoflake errors, see above for details.
To run autoflake locally do e.g.
    pip install autoflake
    autoflake --remove-duplicate-keys <filename>.py
EOF
fi    

########################################################################
if [ "$EFAIL" ]; then FAIL=True; cat <<EOF

----------------------------------------------------
ERROR: Found $EFAIL pep8 errors, see above for details.
To find errors locally do e.g. "flake8 --select=E <filename>.py"

EOF
fi    

########################################################################
if [ "$FFAIL" ]; then FAIL=True; cat <<EOF

----------------------------------------------------
ERROR: Found $FFAIL flake8 errors, see above for details.
To find errors locally do e.g. "flake8 --select=F <filename>.py"

EOF
fi    


########################################################################
cat <<EOF

------------------------------------------------------------------------------
NOTE: To skip flake tests for a given line, can add '# noqa' at the end, e.g.

    if name == "main": garnet_amber.main()   # noqa


EOF

if [ "$FAIL" ]; then
    exit 13
else
    echo "No errors found, hooray!"
fi


##############################################################################
# OLD

# which activate
# exit



# LOCAL_TEST=
# LOCAL_TEST=True

# Gather the python files
# [ "$LOCAL_TEST" ] && cd /nobackup/steveri/github/garnet
# files=`git ls-tree -r HEAD --name-only | egrep 'py$' | sort`

# set -x
