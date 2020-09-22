#!/bin/bash

# Find (and delete) all top-level files in /sim/tmp older than one
# week and owned by buildkite-agent

files=(`find /sim/tmp -mindepth 1 -maxdepth 1 -user buildkite-agent -mtime +7`)
nfiles=${#files[@]}
echo "--- CLEANUP /SIM/TMP: $nfiles OBJECTS owned by buildkite-agent"
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

exit

# TEST: These should yield the same (exc. one extra for 'find')
# find /sim/tmp -mindepth 1 -maxdepth 1  | wc -l
# \ls -ad /sim/tmp/{*,.??*} | wc -l
