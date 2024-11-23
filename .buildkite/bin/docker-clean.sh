#!/bin/bash

# I wrote this script because r7cad-docker was rife with stale old
# docker containers and images. It gets rid of anything with a label
# "deleteme" that is more than a few hours old.
#
# To see it in action visit e.g. the "Delete container" step of
# this buildkite pipeline: https://buildkite.com/stanford-aha/garnet/builds/4803

# More compact version of "docker ps"
function dps() {
    docker ps \
        | sed 's/    //' \
        | sed 's/                        \([^ ]*\)$/    \1/'
}
echo '+++ BEFORE'; dps; printf '\n'

# Kill any container with 'deleteme' in its name AND whose ps matches the given pattern.
function deldocks() {
  pat="$1"
  # echo '------------------------------------------------------------------------'
  dps | grep deleteme | egrep "$pat" || return
  echo '---'
  docker ps | grep deleteme | egrep "$pat" | awk '{print $1}' | xargs echo docker kill
  docker ps | grep deleteme | egrep "$pat" | awk '{print $1}' | xargs docker kill
  printf '\n'
}

# Get rid of all 'deleteme' containers that are months old
echo '+++ MONTHS'
deldocks 'months ago'

# Get rid of all 'deleteme' containers that are weeks old
echo '+++ WEEKS'
deldocks 'weeks ago'

# Allow at least 5 days for very long-running tasks to clear (e.g. aha full regression)
echo '+++ DAYS'
deldocks '[56789] days ago'

# DO NOT kill containers less than one day old.
# This can destory e.g. in-progress 19-hour aha regressions...
# deldocks '[456789] hours ago'

echo '+++ AFTER'; dps; printf '\n'
