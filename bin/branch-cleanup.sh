#!/bin/bash

sq="'"
HELP='
Use this tool to help clean up garnet branches.  For each branch,
shows when/whether the branch was ever merged into master, plus the
diff between the branch head and the merge point.

Usage:
    cd $GARNET_HOME; '$0'

Sample output:
    civde2                 2e4ea93d steveri (1 year, 7 months ago)
    ==> Searched last 10 commits, no merge to master

    lake_dac               5e9eadce mstrange (1 year, 6 months ago)
    ==> MERGED: at lake_dac HEAD~1 (5e9eadce).
    ==> DIFF: git diff 5e9eadce 52815c43 | wc -l: 1528
    ==> TO DELETE: git push origin :lake_dac; \

    power_TA               0109be22 mstrange (1 year, 6 months ago)
    ==> MERGED: at power_TA HEAD~0 (0109be22).
    ==> DIFF: git diff 0109be22 0109be22 | wc -l: 0
    ==> TO DELETE: git push origin :power_TA; \

    pwr-flow-validation    e475d252 Ankita (1 year, 4 months ago)
    ==> MERGED: at pwr-flow-validation HEAD~1 (e475d252).
    ==> DIFF: git diff e475d252 ea524c85 | wc -l: 43
    ==> TO DELETE: git push origin :pwr-flow-validation; \

Interpretation:

* "power_ta" branch is safest to delete, because its head commit was
fully merged to master. Delete by doing "git push origin :power_TA"

* "pwr-flow-validation" is probably safe to merge, since its diff with
  master is small at the merge point (just 43 lines)

* "lake_dac" is very old but it also has a LOT of unmerged changes;
  can see the changes by doing "git diff 5e9eadce 52815c43"

To find all the fully merged branches can do something like:

    '$0' > branch-cleanup.log
    cat branch-cleanup.log | awk '$sq'
      /^[^ ]/ { print; branch=$1; who=$3 }
      /DIFF/ { print; diff=$0; print "" }
      /: 0/ { printf("MERGED %-30s %-13s %s\n", branch, who, diff) }
    '$sq' | grep MERGED

    MERGED gf12-glb         Taeyoung DIFF git diff 7b2e1d6b 7b2e1d6b | wc -l: 0
    MERGED add_array_option Po-Han   DIFF git diff b96ebe5d b96ebe5d | wc -l: 0
    MERGED glb-rv           Taeyoung DIFF git diff f91d4336 f91d4336 | wc -l: 0

'
if [ "$1" == "--help" ]; then
    echo "$HELP"
    exit
fi
date; echo ""

# 1. Get all branches in order from oldest to newest.

f1='%(authordate:short)'
f2='%(refname)'
f3='%(authorname)'
f4='(%(authordate:relative))'
f5='%(objectname)'

# authorname is sus, sometimes comes up as "root"; use authoremail instead
# f="${f1};${f2};${f3};${f4};${f5}"
# # 2020-11-18;lake_dac;mstrange;(1 year, 6 months ago);5e9ead...

f3='%(authoremail)'
f="${f1};${f2};${f3};${f4};${f5}"
# 2024-02-02;refs/heads/pnr-sort;<steveri@steveri.com>;(5 hours ago);d7282e9...

# <37133768+mcoduoza@users.noreply.github.com> => "mcoduoza"
#  | sed 's/<[0-9]*[+]*//' | sed 's/@.*>//'

git branch -va --format="$f" \
    | sort -n | grep remotes | sed 's/;refs.remotes.origin./;/' \
    | sed 's/<[0-9]*[+]*//' | sed 's/@.*>//' \
    | while read line; do 
       echo "$line" | awk -F';' '{
         hash=substr($5,1,8);
         printf("%-30s %s %s %s\n", substr($2,1,30), hash, substr($3,1,15), $4);
       }'
#        echo "$line";
       branch=$(echo "$line" | cut -d";" -f2)
       hash=$(echo "$line"   | cut -d";" -f5)
#        echo "hash $hash, branch '$branch'"

#        echo git log master \| grep $hash
#        git log master | egrep "^commit $hash"
#        git log remotes/origin/$branch | head -1

       commits=$(
         git log remotes/origin/$branch | egrep ^commit | head | awk '{print $2}'
       )
       HEAD=$(
         git log remotes/origin/$branch | egrep ^commit | head -1 | awk '{print $2}'
       )
       i=0; found=''
       for c in $commits; do 
           if git log master | grep $c > /dev/null; then
               h1=`echo $HEAD | cut -b 1-8`
               h2=`echo $c    | cut -b 1-8`
               echo   "  MERGED   at $branch HEAD~$i ($h)."; found=true
               printf "  DIFF     git diff %s %s | wc -l: %s\n" \
                      $h1 $h2 `git diff $HEAD $c | wc -l`
               f=branch-cleanup-logs/$branch.diff
               echo   "  SAVE & DELETE (cut'n'paste')"
               printf "    (set -x; git diff %s %s) >& $f\n" $h1 $h2
               echo   "    git push origin :$branch"
               break
           fi
           ((i+=1))
       done
       if [ "$found" != "true" ]; then
           echo "  Searched last $i commits, no merge to master"
       fi
       echo ""
    done

##############################################################################
# EXAMPLE:
#
#    civde2                         2e4ea93d steveri (3 years, 3 months ago)
#      Searched last 10 commits, no merge to master
#    
#    # Find first non-steveri commit in log: c=7798aa
#    $ git checkout origin/civde2
#    $ git log    # first non-steveri => c=7798aa01b28fe90fbefc7333c4102679ba2b3a7f
#    
#    # Does commit exist in master? => yes
#    $ git log master | grep 7798aa01b28fe90fbefc7333c4102679ba2b3a7f
#    commit 7798aa01b28fe90fbefc7333c4102679ba2b3a7f
#    
#    # How many files in the diff?
#    $ git diff $c | difflast
#    mflowgen/bin/bigtest.sh
#    mflowgen/bin/buildchip.sh
#    mflowgen/bin/setup-buildkite.sh
# 
# etc.
