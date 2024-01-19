#!/bin/bash

function which() { type $*; }
# which activate
# exit



LOCAL_TEST=
LOCAL_TEST=True

# Gather the python files
[ "$LOCAL_TEST" ] && cd /nobackup/steveri/github/garnet
files=`git ls-tree -r HEAD --name-only | egrep 'py$' | sort`

# Fire up a venv if needed
if [ "$LOCAL_TEST" ]; then
  python -c 'import sys; print(sys.prefix)'
  which activate || source /nobackup/steveri/github/smart-components/env/bin/activate
fi

########################################################################
# AUTOFLAKE

DO_AF=True
if [ "$DO_AF" == True ]; then
    echo '--- AUTOFLAKE\n'

    # Install if needed
    which autoflake || echo pip install autoflake

    # Prevent unwanted logfile escape sequences
    filter='s/^---/ ---/;s/^+++/ +++/'

    AF_FAIL=True
    autoflake --remove-duplicate-keys $files | sed "$filter" | grep . || AF_FAIL=

    # autoflake --remove-duplicate-keys codegen/io_placement.py
fi

########################################################################
# FLAKE8

DO_F8err=True
if [ "$DO_F8err" == True ]; then
    # Install if needed
    which flake8 || echo pip install flake8

    # ERRORS
    echo '--- FLAKE8 ERRORS\n'

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

echo '--- FLAKE8 WARNINGS\n'
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
flake8 $files | awk -F ":" "$awkscript"

########################################################################
# Process failures
echo "+++ SUMMARY"
FAIL=

if [ "$AF_FAIL" ]; then
    FAIL=True
    cat <<EOF

ERROR found autoflake errors, see above for details.

To run autoflake locally do e.g.
    pip install autoflake
    autoflake --remove-duplicate-keys <filename>.py

EOF
fi    

if [ "$F8_FAIL" ]; then
    FAIL=True
    cat <<EOF

ERROR found flake8 errors, see above for details.

To run flake8 locally do e.g.
    pip install flake8
    flake8 --select=F <filename>.py
    flake8 <filename>.py

EOF
fi    

if [ "$FAIL" ]; then
    exit 13
else
    echo "No errors found, hooray!"
fi


##############################################################################
# OLD

# Note it is MUCH faster to do files all at once vs. in a for loop
# for f in $files; do
#     printf '\n---\n'
#     nwarns=`flake8 $f | wc -l`
#     printf "%-24s %8d\n" $f $nwarns

cat <<EOF | filter
SPARSE_TESTS/copy_formatted.py:3:1: F401 'subprocess' imported but unused
SPARSE_TESTS/copy_formatted.py:32:11: F541 f-string is missing placeholders
SPARSE_TESTS/generate_tile_files.py:3:1: F401 'subprocess' imported but unused
accumulation.py:7:1: F401 'sam.onyx.generate_matrices.MatrixGenerator' imported but unused
cgra/__init__.py:1:1: F401 '.util.create_cgra' imported but unused
cgra/__init__.py:1:1: F401 '.util.compress_config_data' imported but unused
cgra/__init__.py:2:1: F401 '.wiring.glb_glc_wiring' imported but unused
cgra/__init__.py:2:1: F401 '.wiring.glb_interconnect_wiring' imported but unused
EOF
# exit

echo 'foooooooooooooooooooooooo'
# set -x

# flake8 --select=F $files | filter | tee /dev/tty | grep foo
# exit


exit


flake8 --select=F $files | filter | tee /dev/tty | grep -s F || F8_FAIL=False
exit

flake8 --select=F $files | filter | tee /dev/stdout | grep -s F || F8_FAIL=False
exit



F8_FAIL=True
for f in $files; do
    echo $f
    flake8 --select=F $f | grep . || F8_FAIL=False
    printf '\n'
done

exit
