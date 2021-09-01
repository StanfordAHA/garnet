#!/bin/bash

# Only works for buildkite-agent, duh.
if [ "$USER" != "buildkite-agent" ]; then
    printf "***ERROR Cleanup only works for USER=buildkite-agent\n\n"
    exit 13
fi

# Nondestructive script for helping to clean out /tmp after buildkite run(s)
# Must be used interactively; echoes a bunch of commands that you then have
# to cut'n'paste or source or something by hand ish.

function hour_old {
    find /tmp -mindepth 1 -maxdepth 1 -user buildkite-agent -name "$1" \
         -mmin +1 |& grep -v 'Permission denied'
}
function day_old {
    find /tmp -mindepth 1 -maxdepth 1 -user buildkite-agent -name "$1" \
         -mtime +1 |& grep -v 'Permission denied'
}
function week_old_all {
    find /tmp -mindepth 1 -maxdepth 1 -user buildkite-agent \
         -mtime +7 |& grep -v 'Permission denied'
}

########################################################################
# Find (and delete) all top-level files in /sim/tmp older than one
# week and owned by buildkite-agent
# 
# files=(`find /sim/tmp -mindepth 1 -maxdepth 1 -user buildkite-agent -mtime +7`)
files=(`week_old_all`)
nfiles=${#files[@]}
echo "--- CLEANUP /SIM/TMP: found $nfiles week-old OBJECTS owned by buildkite-agent"
echo "Found $nfiles buildkite-agent files in /sim/tmp older than one week"
if [ "$nfiles" != "0" ]; then echo "Deleting old files..."; fi
for f in ${files[@]}; do
    test -e $f || printf "Oops cannot locate file '$f'\n"
    test -e $f && echo /bin/rm -rf $f && /bin/rm -rf $f
done
echo ""


########################################################################
# step-alias debris can pile up quickly if not maintained
# files=(`find /tmp -user buildkite-agent -name deleteme.step_alias.\* -mmin +60`)
files=(`hour_old deleteme.step_alias.\*`)
nfiles=${#files[@]}
echo "--- CLEANUP /TMP: found $nfiles step-alias files > 1 hour old"
if [ "$nfiles" != "0" ]; then echo "Deleting step-alias files..."; fi
for f in ${files[@]}; do
    test -e $f || printf "Oops cannot locate file '$f'\n"
    test -e $f && echo /bin/rm -rf $f && /bin/rm -rf $f
done
echo ""


########################################################################
# A single run can build up to 48 of these stupid qrc files...
# files=(`find /tmp -user buildkite-agent -name qrc\* -mtime +1`)
files=(`day_old qrc\*`)
nfiles=${#files[@]}
echo "--- CLEANUP /TMP: found $nfiles qrc log files > 1 day old"
if [ "$nfiles" != "0" ]; then echo "Deleting qrc log files..."; fi
for f in ${files[@]}; do
    test -e $f || printf "Oops cannot locate file '$f'\n"
    test -e $f && echo /bin/rm -rf $f && /bin/rm -rf $f
done
echo ""


########################################################################
# Don't even know what these are, but they build up and are annoying
# files=(`find /tmp -user buildkite-agent -name tmp.deleteme.\* -mmin +60`)
files=(`hour_old tmp.deleteme.\*`)
nfiles=${#files[@]}
echo "--- CLEANUP /TMP: found $nfiles tmp.deleteme files > 1 hour old"
if [ "$nfiles" != "0" ]; then echo "Deleting tmp.deleteme files..."; fi
for f in ${files[@]}; do
    test -e $f || printf "Oops cannot locate file '$f'\n"
    test -e $f && echo /bin/rm -rf $f && /bin/rm -rf $f
done
echo ""


