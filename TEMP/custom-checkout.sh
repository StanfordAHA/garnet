#!/bin/bash
set +x # debug OFF

pwd
env
cd $BUILDKITE_BUILD_PATH 

########################################################################
echo "+++ checkout.sh trash"
echo '-------------'
ls -l /tmp/ahaflow-custom-checkout* || echo nope
echo '-------------'
ls -ld /var/lib/buildkite-agent/builds/*/stanford-aha/aha-flow/ || echo nope
echo '-------------'
ls -ld /var/lib/buildkite-agent/builds/*/stanford-aha/aha-flow/aha || echo nope
echo '-------------'
who am i
whoami

echo "--- CONTINUE"
########################################################################

# FIXME/NOTE! can skip a lot of stuff by checking to see if
# $FLOW_REPO / $FLOW_HEAD_SHA already been set

# git remote set-url origin https://github.com/hofstee/aha
if ! git remote set-url origin https://github.com/hofstee/aha 2> /dev/null; then
  test -e aha || git clone https://github.com/hofstee/aha
  cd aha
  git remote set-url origin https://github.com/hofstee/aha
fi

git submodule foreach --recursive "git clean -ffxdq"
git clean -ffxdq

unset FAIL
# FAIL means build was triggered by foreign (non-aha) repo, i.e. one of the submods
echo git fetch -v --prune -- origin $BUILDKITE_COMMIT
git fetch -v --prune -- origin $BUILDKITE_COMMIT || FAIL=true

# AMBER_DEFAULT_BRANCH=no-heroku
AMBER_DEFAULT_BRANCH=master
[ "$FAIL" ] && git fetch -v --prune -- origin $AMBER_DEFAULT_BRANCH || echo okay

git checkout -f FETCH_HEAD
git submodule sync --recursive
git submodule update --init --recursive --force
git submodule foreach --recursive "git reset --hard"

[ "$FAIL" ] && echo "--- Handle PR"
echo "--- Looking for submod commit $BUILDKITE_COMMIT"
unset FOUND_SUBMOD
[ "$FAIL" ] && for submod in garnet Halide-to-Hardware lassen gemstone canal lake; do
    echo "--- - " Looking in submod $submod
    # (cd $submod; git checkout $BUILDKITE_COMMIT && echo UPDATE SUBMOD $submod || echo NOT $submod);
    (set -x; cd $submod; git fetch origin && git checkout $BUILDKITE_COMMIT) && FOUND_SUBMOD=true || echo "--- -- NOT " Ssubmod
    [ "$FOUND_SUBMOD" ] && echo "--- -- FOUND " $submod
    [ "$FOUND_SUBMOD" ] && break
done || echo okay no submod updates needed

# # want?
if [ "$FOUND_SUBMOD" ]; then
    # These are used later by pipeline.xml
    # BUT NOT as global env vars; this script must
    # be sourced in same scope as var usage, see?
    FLOW_REPO=$submod
    FLOW_REPO_SHA=$BUILDKITE_COMMIT
fi


# https://github.com/StanfordAHA/garnet/blob/aha-flow-no-heroku/TEMP/custom-checkout.sh
# https://raw.githubusercontent.com/StanfordAHA/garnet/aha-flow-no-heroku/TEMP/custom-checkout.sh
# curl -s https://raw.githubusercontent.com/StanfordAHA/garnet/aha-flow-no-heroku/TEMP/custom-checkout.sh > /tmp/tmp
# BUILDKITE_BUILD_NUMBER

# Temporarily, for dev purposes, load pipeline from garnet repo;
# later replace aha repo .buildkite/pipeline.yml w dev from garnet, see?

u=https://raw.githubusercontent.com/StanfordAHA/garnet/aha-flow-no-heroku/TEMP/pipeline.yml

ls -l .buildkite/pipeline.yml
curl -s $u > .buildkite/pipeline.yml
ls -l .buildkite/pipeline.yml

pwd
ls -l .buildkite || echo nop
ls -l .buildkite/hooks || echo nop

