#!/bin/bash

set -x

# Verilator must be 5.028 or better maybe
function insufficient { awk "BEGIN {if ($1 < 5.028) exit(0); else exit(13)}"; }


# E.g. verilator --version = "Verilator 5.032 2025-01-01 rev (Debian 5.032-1)"
if ! verilator --version >& /dev/null; then version=0.0
else version=$(verilator --version |& cut -d " " -f2); fi

if insufficient $version; then

    # Only works with g++-10 else "unrecognized option ‘-fcoroutines’"
    yes | (apt update; apt upgrade; apt install g++-10)
    (cd /usr/bin; test -e g++ && mv g++ g++.orig; ln -s g++-10 g++)

    # Add target version to apt sources: "plucky" should get us version 5.032
    cp -p /etc/apt/sources.list /etc/apt/sources.list.bak
    REPO="deb http://archive.ubuntu.com/ubuntu/ plucky main universe"
    echo $REPO >> /etc/apt/sources.list
    diff /etc/apt/sources.list.bak /etc/apt/sources.list
    apt update

    # Install verilator
    apt policy verilator
    yes | apt install -t plucky verilator
    verilator --version
fi



