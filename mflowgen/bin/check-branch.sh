#!/bin/bash
# Assumes script lives in $garnet/mflowgen/bin

function Help {
    cat <<EOF

Usage: $0 <regex>

Description:
  If current garnet branch does not match regex, exit with error status 13.

Examples:
    $0 master      || exit ; # Only proceed if branch is master branch.
    $0 'test[0-9]' || exit ; # Only proceed on branches 'test1', 'test2', ...
EOF
}

if [ "$1" == "" ]; then Help; exit 13; fi

########################################################################
# Find garnet repo '$garnet'. Assumes script lives in $garnet/mflowgen/bin
function where_this_script_lives {
    # Where this script lives
    s=${BASH_SOURCE[0]}
    scriptpath=$s      # E.g. "build_tarfile.sh" or "foo/bar/build_tarfile.sh"
    scriptdir=${s%/*}  # E.g. "build_tarfile.sh" or "foo/bar"
    if test "$scriptdir" == "$scriptpath"; then scriptdir="."; fi
    # scriptdir=`cd $scriptdir; pwd`
    (cd $scriptdir; pwd)
}
script_home=`where_this_script_lives`
garnet=`cd $script_home/../..; pwd`
echo "Found garnet='$garnet'; hope that's correct...!"


########################################################################
branch_filter="$1"

echo '+++ BRANCH FILTER'
echo ""
echo "Note tests only work in branches that match regexp '$branch_filter'"
if [ "$BUILDKITE_BRANCH" ]; then
    branch=${BUILDKITE_BRANCH}
    echo "It looks like we are running from within buildkite"
    echo "And it looks like we are in branch '$branch'"

else 
    # branch=`git symbolic-ref --short HEAD` ; # ?? this doesn't look right?
    branch=`cd $garnet; git symbolic-ref --short HEAD`
    echo "It looks like we are *not* running from within buildkite"
    echo "We appear to be in branch '$branch'"
fi
echo ""

# Note DOES NOT WORK if $branch_filter is in quotes e.g. "$branch_filter" :o
if [[ "$branch" =~ $branch_filter ]]; then
    echo "Okay that's the right branch, off we go."
    exit
else
    # Test is disabled for this branch, emit a polite info message and leave.
    if [ "$BUILDKITE_LABEL" ]; then
        # https://buildkite.com/docs/agent/v3/cli-annotate
        cmd="buildkite-agent annotate --append"
        label="$BUILDKITE_LABEL"
    else
        cmd='cat'
        label=${modlist[0]}
    fi

    ems='!!!'
    echo "NOTE '$label' TEST DID NOT ACTUALLY RUN$ems"$'\n' | $cmd
    # echo "- Tests only work in branch '$allowed_branch'" | $cmd
    echo "- This test is disabled except for branches that match regex '$branch_filter'" | $cmd
    echo "- and we appear to be in branch '$branch'"$'\n' | $cmd
    exit 13
fi
