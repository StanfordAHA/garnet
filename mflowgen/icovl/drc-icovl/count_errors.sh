#!/bin/bash

# Example / usage:
# count_errors.sh drc.summary
#   ICOVL   0 errors in  0 different categories
#   DTCD  156 errors in  6 different categories
#       RULECHECK DTCD.DN.4 ..................... TOTAL Result Count = 26   (26)
#       RULECHECK DTCD.DN.5:TCDDMY_V2 ........... TOTAL Result Count = 26   (26)
#       RULECHECK DTCD.DN.5:TCDDMY_V3 ........... TOTAL Result Count = 26   (26)
#       RULECHECK DTCD.DN.5:TCDDMY_V4 ........... TOTAL Result Count = 26   (26)
#       RULECHECK DTCD.DN.5:TCDDMY_V5 ........... TOTAL Result Count = 26   (26)
#       RULECHECK DTCD.DN.5:TCDDMY_V6 ........... TOTAL Result Count = 26   (26)

ncat=`egrep '^    RULECHECK ICOVL' $1 | wc -l`
if [ "$ncat" == "" ]; then ncat=0; fi
nres=`egrep '^    RULECHECK ICOVL' $1 | awk 'BEGIN{n=0} {n+=$(NF-1)} END {print n}'`
printf "%-5s %3d errors in %2d different categories\n" ICOVL $nres $ncat
egrep '^    RULECHECK ICOVL' $1
# echo ""

ncat=`egrep '^    RULECHECK DTCD' $1 | wc -l`
if [ "$ncat" == "" ]; then ncat=0; fi
nres=`egrep '^    RULECHECK DTCD' $1 | awk 'BEGIN{n=0} {n+=$(NF-1)} END {print n}'`
printf "%-5s %3d errors in %2d different categories\n" DTCD $nres $ncat
egrep '^    RULECHECK DTCD' $1

echo ""
