#!bin/bash

unset FAIL
git remote set-url origin https://github.com/hofstee/aha
git submodule foreach --recursive "git clean -ffxdq"
git clean -ffxdq
set -x; echo git fetch -v --prune -- origin $BUILDKITE_COMMIT

# set -x; git fetch -v --prune -- origin $BUILDKITE_COMMIT || git fetch -v --prune -- origin master
set -x; git fetch -v --prune -- origin $BUILDKITE_COMMIT || FAIL=true
[ "$FAIL" ] && git fetch -v --prune -- origin master

git checkout -f FETCH_HEAD
git submodule sync --recursive
git submodule update --init --recursive --force
git submodule foreach --recursive "git reset --hard"

[ "$FAIL" ] && for submod in garnet Halide-to-Hardware lassen gemstone canal lake; do
    (cd $submod; git checkout $BUILDKITE_COMMIT && echo UPDATE SUBMOD $submod || echo NOT $submod);
done;

