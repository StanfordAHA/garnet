#!/bin/bash

mkdir outputs/tile_tbs

python3 generate_testbench.py

cp testbench.sv outputs/testbench.sv
cp cmd.tcl outputs/cmd.tcl
