#!/bin/bash

python3 generate_test_vectors.py

if [ $PWR_AWARE == False ]; then
    cat defines.v TilePETb.sv > outputs/testbench.sv
else
    cat defines.v TilePETb_PD.sv > outputs/testbench.sv
fi

cp test_vectors.txt outputs/test_vectors.txt
cp test_outputs.txt outputs/test_outputs.txt
cp cmd.tcl outputs/cmd.tcl
