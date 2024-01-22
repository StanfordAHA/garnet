#!/bin/bash

# More compact version of "docker ps"
function dps() {
    docker ps \
        | sed 's/    //' \
        | sed 's/                        \([^ ]*\)$/    \1/'
}
echo '+++ BEFORE'; dps


function deldocks() {
  pat="$1"
  # echo '------------------------------------------------------------------------'
  dps | grep deleteme | egrep "$pat" || return
  echo '------------------------------------------------------------------------'
  docker ps | grep deleteme | egrep "$pat" | awk '{print $1}' | xargs echo docker kill
  # docker ps | grep deleteme | egrep "$pat" | awk '{print $1}' | xargs echo docker kill
}

echo '+++ MONTHS'
deldocks 'months ago'

echo '+++ WEEKS'
deldocks 'weeks ago'

echo '+++ DAYS'
deldocks 'days ago'

echo '+++ HOURS'
deldocks '[456789] hours ago'

# docker ps | grep deleteme | grep 'months ago'
# docker ps | grep deleteme | grep 'months ago' | awk '{print $1}' | xargs docker kill
# 
# docker ps | grep deleteme | grep 'weeks ago'
# docker ps | grep deleteme | grep 'weeks ago'  | awk '{print $1}' | xargs docker kill
# 
# docker ps | grep deleteme | grep 'days ago'
# docker ps | grep deleteme | grep 'days ago'   | awk '{print $1}' | xargs docker kill
# 
# docker ps | grep deleteme | egrep '[456789] hours ago'
# docker ps | grep deleteme | egrep '[456789] hours ago' | awk '{print $1}' | xargs docker kill
