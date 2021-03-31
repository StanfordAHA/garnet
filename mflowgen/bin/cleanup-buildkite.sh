#!/bin/bash

########################################################################
# Find (and delete) all top-level files in /sim/tmp older than one
# week and owned by buildkite-agent

files=(`find /sim/tmp -mindepth 1 -maxdepth 1 -user buildkite-agent -mtime +7`)
nfiles=${#files[@]}
echo "--- CLEANUP /SIM/TMP: found $nfiles week-old OBJECTS owned by buildkite-agent"
echo "Found $nfiles buildkite-agent files in /sim/tmp older than one week"

if [ "$nfiles" == "0" ]; then exit 0; fi

# Show newest and oldest objects found
echo "";\
ls -ltd ${files[@]} | tail -1;\
ls -ltd ${files[@]} | head -1

echo "";\
echo "Deleting old files..."
for f in ${files[@]}; do
    echo /bin/rm -rf $f
    /bin/rm -rf $f
done

########################################################################
# step-alias debris can pile up quickly if not maintained
files=(`find /tmp -user buildkite-agent -name deleteme.step_alias.\* -mmin +60`)
nfiles=${#files[@]}
echo "--- CLEANUP /TMP: found $nfiles step-alias files > 1 hour old"
echo ""; echo "Deleting step-alias files..."
for f in ${files[@]}; do
    echo /bin/rm -rf $f; /bin/rm -rf $f
done

########################################################################
# A single run can build up to 48 of these stupid qrc files...
files=(`find /tmp -user buildkite-agent -name qrc\* -amin +1`)
nfiles=${#files[@]}
echo "--- CLEANUP /TMP: found $nfiles qrc log files > 1 day old"
echo ""; echo "Deleting qrc log files..."
for f in ${files[@]}; do
    echo /bin/rm -rf $f; /bin/rm -rf $f
done

########################################################################
# Don't even know what these are, but they build up and are annoying
files=(`find /tmp -user buildkite-agent -name tmp.deleteme.\* -mmin +60`)
nfiles=${#files[@]}
echo "--- CLEANUP /TMP: found $nfiles tmp.deleteme files > 1 hour old"
echo ""; echo "Deleting tmp.deleteme files..."
for f in ${files[@]}; do
    echo /bin/rm -rf $f; /bin/rm -rf $f
done


exit

# TEST: These should yield the same (exc. one extra for 'find')
# find /sim/tmp -mindepth 1 -maxdepth 1  | wc -l
# \ls -ad /sim/tmp/{*,.??*} | wc -l
