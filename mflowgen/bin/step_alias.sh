#!/bin/bash
# Function to expand step aliases
# Uses output of "make list" from a valid mflowgen step, e.g.
#   % cd /build/gold.93/full_chip
#   % make list | step_alias.sh syn
#       synopsys-dc-synthesis

if [[ -t 0 ]]; then
    echo "Oops you forgot to give me 'make list' info"
    echo "Examples:"
    echo "    make list | $0 syn"
    echo "    make list > tmp.txt; $0 syn < tmp.txt"
    echo ""
    exit 13
fi

# Siphon stdin off to temp file for safekeeping
makelist=/tmp/deleteme.step_alias.$$
cat > $makelist

# E.g. 'step_alias.sh syn' returns 'synopsys-dc-synthesis' or
# 'cadence-genus-synthesis' as appropriate

if [ "$1" == "" ]; then
    echo "***ERROR: no step arg provided to '$0'"
    echo "Usage: make list | $0 <step>"
    exit 13
fi

case "$1" in
    # This is probably dangerous; init is heavily overloaded
    init)      s=cadence-innovus-init      ;;

    # "synthesis" will expand to dc or genus according to what's
    # in "make list" (see below). Same for gdsmerge etc.
    dragon)    s=dragonphy ;;
    syn)       s=synthesis ;;
    gds)       s=gdsmerge ;;
    tape)      s=gdsmerge ;;
    merge)     s=gdsmerge ;;
    *)         s="$1" ;;
esac

# 1. First, look for exact match
ntries=1
s1=`cat $makelist |& egrep -- " $s"'$' | awk '{ print $NF; exit }'`

# Then look for alias that expands to synopsys/cadence/mentor tool
# Uses *first* pattern match found in "make list" to expand e.g.
# "synthesis" => "synopsys-dc-synthesis" or "cadence-genus-synthesis"
if ! [ "$s1" ]; then
    ntries=2
    p=' synopsys| cadence| mentor'
    s1=`cat $makelist |& egrep "$p" | egrep -- "$s"'$' | awk '{ print $NF; exit }'`
fi

# Then look for alias that expands to anything that kinda matches
if ! [ "$s1" ]; then
    ntries=3
    s1=`cat $makelist |& egrep -- "$s"'$' | awk '{ print $NF; exit }'`
fi

if ! [ "$s1" ]; then
    echo "**ERROR: Could not find a valid alias for '$1'"
    exit 13
fi

DBG=""; if [ "$DBG" ] ; then
    echo '---'
    echo "FINAL '$s' -> '$s1' (after $ntries tries)"
fi

# Note: returns null ("") if no alias found
echo $s1; # return value = $s1

# Clean up and exit
(test -d $makelist && /bin/rm $makelist) >& /dev/null || echo -n ""
exit 0

##############################################################################
# UNIT TESTS for step_alias, cut'n'paste
cmd=step_alias.sh
test_steps="syn init cts place route postroute gds tape merge gdsmerge lvs drc"
test_steps="constraints MemCore PE rtl synthesis custom-dc-postcompile tsmc16 synthesis foooo"
for s in $test_steps; do echo "'$s' ==> '`$cmd $s`'"; done
for s in $test_steps; do $cmd $s; done

