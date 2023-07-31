#!/bin/bash
set -x

unset FAIL
# git remote set-url origin https://github.com/hofstee/aha

ls .git || echo no git
ls aha/.git || echo no aha git

if ! git remote set-url origin https://github.com/hofstee/aha; then
  test -f aha || git clone https://github.com/hofstee/aha || echo failed TWICE
  cd aha
  git remote set-url origin https://github.com/hofstee/aha
fi

# cd aha || echo no aha
git submodule foreach --recursive "git clean -ffxdq"
git clean -ffxdq
set -x; echo git fetch -v --prune -- origin $BUILDKITE_COMMIT

# set -x; git fetch -v --prune -- origin $BUILDKITE_COMMIT || git fetch -v --prune -- origin master
set -x; git fetch -v --prune -- origin $BUILDKITE_COMMIT || FAIL=true
[ "$FAIL" ] && git fetch -v --prune -- origin master || echo okay

git checkout -f FETCH_HEAD
git submodule sync --recursive
git submodule update --init --recursive --force
git submodule foreach --recursive "git reset --hard"

echo "--- Looking for submod commit $BUILDKITE_COMMIT"
unset FOUND_SUBMOD
[ "$FAIL" ] && for submod in garnet Halide-to-Hardware lassen gemstone canal lake; do
    echo "--- - " Looking in submod $submod
    # (cd $submod; git checkout $BUILDKITE_COMMIT && echo UPDATE SUBMOD $submod || echo NOT $submod);
    (cd $submod; git fetch origin && git checkout $BUILDKITE_COMMIT) && FOUND_SUBMOD=true || echo "--- -- NOT " Ssubmod
    [ "$FOUND_SUBMOD" ] && echo "--- -- FOUND " $submod
    [ "$FOUND_SUBMOD" ] && break
done || echo okay no submod updates needed

# want?
if [ "$FOUND_SUBMOD" ]; then
    export FLOW_REPO=$submod
    export FLOW_REPO_SHA=$BUILDKITE_COMMIT
    export BUILDKITE_COMMIT=master
    export BUILDKITE_COMMIT_MESSAGE="hello woild"
fi


# https://github.com/StanfordAHA/garnet/blob/aha-flow-no-heroku/TEMP/custom-checkout.sh
# https://raw.githubusercontent.com/StanfordAHA/garnet/aha-flow-no-heroku/TEMP/custom-checkout.sh
# curl -s https://raw.githubusercontent.com/StanfordAHA/garnet/aha-flow-no-heroku/TEMP/custom-checkout.sh > /tmp/tmp
# BUILDKITE_BUILD_NUMBER

u=https://raw.githubusercontent.com/StanfordAHA/garnet/aha-flow-no-heroku/TEMP/pipeline.yml

ls -l .buildkite/pipeline.yml
curl -s $u > .buildkite/pipeline.yml
ls -l .buildkite/pipeline.yml

