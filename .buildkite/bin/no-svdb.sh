#!/bin/bash

# Prevent LVS from generating an svdb database, which I've never used
# and which takes up a huge amount of time to generate and space to
# store, and wihch can easily be generated on demand if/when someone
# really wants it.

echo "${0}: removing svdb directives from LVS rule set"

# 1. Remove "MASK SVDB" directives from ruleset

f=inputs/adk/calibre-lvs.rule
if ! test -f $f; then
    echo "WARNING cannot find ruleset $f ; abandoning no-svdb attempt"
    exit
fi

# Want to remove all SVDB directives from rule set
# Note: still need to create SVDB directory or cannot do LVS BOX
#
# BEFORE:
#     % grep SVDB inputs/adk/calibre-lvs.rule 
#     MASK SVDB DIRECTORY "svdb" XRC
#     MASK SVDB DIRECTORY "svdb" XRC SI
#
# AFTER:
#     % grep SVDB inputs/adk/calibre-lvs.rule 
#     MASK SVDB DIRECTORY "svdb"
#     MASK SVDB DIRECTORY "svdb"

cat $f | sed 's/MASK SVDB.*/MASK SVDB DIRECTORY "svdb"/' > ruleset.local
echo ""
echo diff $f ruleset.local
diff $f ruleset.local


# Change runset template to use ruleset.local instead of inputs/adk/...
mv lvs.runset.template lvs.runset.template.orig

cat lvs.runset.template.orig \
    | sed 's|inputs/adk/calibre-lvs.rule|ruleset.local|' \
    > lvs.runset.template

echo ""
echo diff lvs.runset.template.orig lvs.runset.template
diff lvs.runset.template.orig lvs.runset.template
