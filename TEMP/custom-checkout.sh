#!/bin/bash

echo "--- BEGIN CUSTOM CHECKOUT"

# save and restore existing shell opts in case script is sourced
RESTORE_SHELLOPTS="$(set +o)"

set +u # nounset? not on my watch!
set +x # debug OFF

pwd # We are in root dir (/) !!!oh no!!!
echo cd $BUILDKITE_BUILD_PATH
cd $BUILDKITE_BUILD_PATH
pwd

# ########################################################################
# echo "+++ checkout.sh trash"
# echo '-------------'
# ls -l /tmp/ahaflow-custom-checkout* || echo nope
# echo '-------------'
# ls -ld /var/lib/buildkite-agent/builds/*/stanford-aha/aha-flow/ || echo nope
# echo '-------------'
# ls -ld /var/lib/buildkite-agent/builds/*/stanford-aha/aha-flow/aha || echo nope
# echo '-------------'
# echo I am `whoami`
# 
# # No!
# f='/tmp/ahaflow-custom-checkout-$BUILDKITE_BUILD_NUMBER.sh'
# test -f $f && /bin/rm $f
# 
# 
# echo "--- CONTINUE"
# ########################################################################

# FIXME/NOTE! can skip a lot of stuff by checking to see if
# $FLOW_REPO / $FLOW_HEAD_SHA already been set

# set -x
# # git remote set-url origin https://github.com/hofstee/aha
# if ! git remote set-url origin https://github.com/hofstee/aha 2> /dev/null; then
#   test -e aha || git clone https://github.com/hofstee/aha
#   cd aha
#   git remote set-url origin https://github.com/hofstee/aha
# fi
# set +x

# This is what I SHOULD do...
echo "--- CLONE AHA REPO"
cd $BUILDKITE_BUILD_PATH
test -e aha && /bin/rm -rf aha
git clone https://github.com/hofstee/aha
cd aha

git remote set-url origin https://github.com/hofstee/aha
git submodule foreach --recursive "git clean -ffxdq"
git clean -ffxdq

unset PR_FROM_SUBMOD
# PR_FROM_SUBMOD means build was triggered by foreign (non-aha) repo, i.e. one of the submods
echo git fetch -v --prune -- origin $BUILDKITE_COMMIT
git fetch -v --prune -- origin $BUILDKITE_COMMIT || PR_FROM_SUBMOD=true

# AMBER_DEFAULT_BRANCH=no-heroku
AMBER_DEFAULT_BRANCH=master
[ "$PR_FROM_SUBMOD" ] && git fetch -v --prune -- origin $AMBER_DEFAULT_BRANCH || echo okay

git checkout -f FETCH_HEAD
git submodule sync --recursive
git submodule update --init --recursive --force
git submodule foreach --recursive "git reset --hard"

if [ "$PR_FROM_SUBMOD" ]; then
    echo "--- Handle PR"
    echo "--- Looking for submod commit $BUILDKITE_COMMIT"
    unset FOUND_SUBMOD
    for submod in garnet Halide-to-Hardware lassen gemstone canal lake; do
        echo "--- - " Looking in submod $submod
        # (cd $submod; git checkout $BUILDKITE_COMMIT && echo UPDATE SUBMOD $submod || echo NOT $submod);
        (set -x; cd $submod; git fetch origin && git checkout $BUILDKITE_COMMIT) && FOUND_SUBMOD=true || echo "--- -- NOT " Ssubmod
        [ "$FOUND_SUBMOD" ] && echo "--- -- FOUND " $submod
        [ "$FOUND_SUBMOD" ] && break
    done

    # # want?
    if [ "$FOUND_SUBMOD" ]; then
        # These are used later by pipeline.xml
        # BUT NOT as global env vars; this script must
        # be sourced in same scope as var usage, see?
        FLOW_REPO=$submod
        FLOW_REPO_SHA=$BUILDKITE_COMMIT
    else
        echo "ERROR could not find requesting submod"; exit 13
    fi
fi

# https://github.com/StanfordAHA/garnet/blob/aha-flow-no-heroku/TEMP/custom-checkout.sh
# https://raw.githubusercontent.com/StanfordAHA/garnet/aha-flow-no-heroku/TEMP/custom-checkout.sh
# curl -s https://raw.githubusercontent.com/StanfordAHA/garnet/aha-flow-no-heroku/TEMP/custom-checkout.sh > /tmp/tmp
# BUILDKITE_BUILD_NUMBER

# Temporarily, for dev purposes, load pipeline from garnet repo;
# later replace aha repo .buildkite/pipeline.yml w dev from garnet, see?

echo "+++ for now, load pipeline from garnet aha-flow-no-heroku"

echo "BEFORE: " `ls -l .buildkite/pipeline.yml`
u=https://raw.githubusercontent.com/StanfordAHA/garnet/aha-flow-no-heroku/TEMP/pipeline.yml
echo "curl -s $u > .buildkite/pipeline.yml"
      curl -s $u > .buildkite/pipeline.yml
echo "AFTER: " `ls -l .buildkite/pipeline.yml`

# echo "+++ Got hooks?"; ls -l .buildkite/hooks || echo nop

echo "--- RESTORE SHELLOPTS"
eval "$RESTORE_SHELLOPTS"
pwd
