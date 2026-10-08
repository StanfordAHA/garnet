#!/bin/bash
# Fail the step if the generator fails (it used to pass with no testbench.sv).
set -e

mkdir -p outputs/tile_tbs

python3 generate_testbench.py

cp testbench.sv outputs/testbench.sv
cp cmd.tcl outputs/cmd.tcl
