#!/bin/bash

HELP='
DESCRIPTION:
  Look for verilator 5.028 or better; if not found, install it.
  May require sudo privilege.
'
[ "$1" == "--help" ] && echo "$HELP" && exit
# ------------------------------------------------------------------------
set -x

# Verilator must be 5.028 or better maybe
function insufficient { awk "BEGIN {if ($1 < 5.028) exit(0); else exit(13)}"; }


# E.g. verilator --version = "Verilator 5.032 2025-01-01 rev (Debian 5.032-1)"
if ! verilator --version >& /dev/null; then version=0.0
else version=$(verilator --version |& cut -d " " -f2); fi

if insufficient $version; then

    # Only works with g++-10 else "unrecognized option ‘-fcoroutines’"
    echo "--- MAKE SETUP: Install g++-10, autoconf, bison, help2man"
    yes | (apt update; apt upgrade; apt install g++-10)
    (cd /usr/bin; test -e g++ && mv g++ g++.orig; ln -s g++-10 g++)
    echo -------------------------------

    echo These are missing in docker ATM 
    yes | apt-get install autoconf
    yes | apt-get install bison
    yes | apt-get install help2man
    echo -------------------------------

    echo "--- MAKE SETUP: Install verilator 5.028"
    cd /usr/share; test -d verilator || git clone https://github.com/verilator/verilator
    cd /usr/share/verilator; git checkout v5.028
    cd /usr/share/verilator; unset VERILATOR_ROOT; autoconf; ./configure

    cd /usr/share/verilator; unset VERILATOR_ROOT; make -j 4 || echo ERROR
    cd /usr/share/verilator; make clean || echo ERROR cannot clean for some reason i guess
    test -e /usr/local/bin/verilator && mv /usr/local/bin/verilator /usr/local/bin/verilator.orig || echo NOT YET
    cd /usr/local/bin; ln -s /usr/share/verilator/bin/verilator
    echo -------------------------------

    verilator --version
fi



