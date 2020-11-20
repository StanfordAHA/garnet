#!/bin/bash

python3 generate_testbench.py

cp testbench.sv outputs/testbench.sv
cp test_vectors.txt outputs/test_vectors.txt
cp test_outputs.txt outputs/test_outputs.txt
cp cmd.tcl outputs/cmd.tcl
