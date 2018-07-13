#!/bin/tcsh
set RTL_FOLDER="./genesis_verif"
rm -rf INCA_libs irun.*
irun -sv -top top -timescale 1ns/1ps -l irun.log -access +rwc -notimingchecks -input ./tests/cmd.tcl ./tests/test_cb_7_8_no_const.v $RTL_FOLDER/cb.v connect_box_width_width_7_num_tracks_8_has_constant0_default_value0_feedthrough_outputs_11111111.v

