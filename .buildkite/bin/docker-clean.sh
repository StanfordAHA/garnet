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


function deldocks() {
  pat="$1"
  # echo '------------------------------------------------------------------------'
  dps | grep deleteme | egrep "$pat" || return
  echo '---'
  docker ps | grep deleteme | egrep "$pat" | awk '{print $1}' | xargs echo docker kill
  docker ps | grep deleteme | egrep "$pat" | awk '{print $1}' | xargs docker kill
  printf '\n'
}

echo '+++ MONTHS'
deldocks 'months ago'

echo '+++ WEEKS'
deldocks 'weeks ago'

echo '+++ DAYS'
# deldocks 'days ago'  # Maybe not enough to avoid 19-hour aha regressions that ran long...
deldocks '[56789] days ago'

# NOT GOOD! This kills e.g. in-progress 19-hour aha regressions...
# echo '+++ HOURS'
# deldocks '[456789] hours ago'

echo '+++ AFTER'; dps; printf '\n'

# docker ps | grep deleteme | grep 'months ago'
# docker ps | grep deleteme | grep 'months ago' | awk '{print $1}' | xargs docker kill
