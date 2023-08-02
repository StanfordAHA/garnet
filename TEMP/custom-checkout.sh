#!/bin/bash

echo "--- BEGIN CUSTOM CHECKOUT"

# save and restore existing shell opts in case script is sourced
RESTORE_SHELLOPTS="$(set +o)"

set +u # nounset? not on my watch!
set +x # debug OFF

# BUILDKITE_BUILD_CHECKOUT_PATH=/var/lib/buildkite-agent/builds/r7cad-docker-1/stanford-aha/aha-flow
echo I am now in dir `pwd` # We are in root dir (/) !!!oh no!!!
echo cd $BUILDKITE_BUILD_CHECKOUT_PATH
cd $BUILDKITE_BUILD_CHECKOUT_PATH

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

set -x
ls -l aha/.buildkite/hooks || echo nop
grep foo aha/.buildkite/hooks/* || echo nop

test -e aha && /bin/rm -rf aha

ls -l aha/.buildkite/hooks || echo nop
grep foo aha/.buildkite/hooks/* || echo nop


git clone https://github.com/hofstee/aha
ls -l aha/.buildkite/hooks || echo nop
grep foo aha/.buildkite/hooks/* || echo nop
set +x

cd aha



git remote set-url origin https://github.com/hofstee/aha
git submodule foreach --recursive "git clean -ffxdq"
git clean -ffxdq

unset PR_FROM_SUBMOD
# PR_FROM_SUBMOD means build was triggered by foreign (non-aha) repo, i.e. one of the submods
echo git fetch -v --prune -- origin $BUILDKITE_COMMIT
if git fetch -v --prune -- origin $BUILDKITE_COMMIT; then
    echo "Checked out aha commit '$BUILDKITE_COMMIT'"
else
    echo 'Requested commit does not exist in aha repo'
    echo 'This must be a pull request from one of the submods'
    PR_FROM_SUBMOD=true

    # AHA_DEFAULT_BRANCH=no-heroku
    AHA_DEFAULT_BRANCH=master
    echo "Meanwhile, will use default branch '$AHA_DEFAULT_BRANCH' for aha repo"
    git fetch -v --prune -- origin $AHA_DEFAULT_BRANCH
fi

echo '+++ HOOKS'
pwd
ls -l aha/.buildkite/hooks || echo nop
grep foo aha/.buildkite/hooks/* || echo nop


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

echo '+++ HOOKS 124'
pwd
ls -l aha/.buildkite/hooks || echo nop
grep foo aha/.buildkite/hooks/* || echo nop

# https://github.com/StanfordAHA/garnet/blob/aha-flow-no-heroku/TEMP/custom-checkout.sh
# https://raw.githubusercontent.com/StanfordAHA/garnet/aha-flow-no-heroku/TEMP/custom-checkout.sh
# curl -s https://raw.githubusercontent.com/StanfordAHA/garnet/aha-flow-no-heroku/TEMP/custom-checkout.sh > /tmp/tmp
# BUILDKITE_BUILD_NUMBER

# Temporarily, for dev purposes, load pipeline from garnet repo;
# later replace aha repo .buildkite/pipeline.yml w dev from garnet, see?

echo "+++ FOR NOW, load pipeline from garnet aha-flow-no-heroku"

echo "BEFORE: " `ls -l .buildkite/pipeline.yml`
u=https://raw.githubusercontent.com/StanfordAHA/garnet/aha-flow-no-heroku/TEMP/pipeline.yml
echo "curl -s $u > .buildkite/pipeline.yml"
      curl -s $u > .buildkite/pipeline.yml
echo "AFTER:  " `ls -l .buildkite/pipeline.yml`

echo "+++ WHAT IS UP WITH THE HOOKS?"
set -x
echo '--------------'
git branch
echo '--------------'
git status -uno
ls -l .buildkite/hooks || echo nop
cat .buildkite/hooks/post-checkout || echo hop
set +x

echo '+++ HOOKS 155'
pwd
ls -l aha/.buildkite/hooks || echo nop
grep foo aha/.buildkite/hooks/* || echo nop




echo "--- RESTORE SHELLOPTS"
eval "$RESTORE_SHELLOPTS"
pwd
