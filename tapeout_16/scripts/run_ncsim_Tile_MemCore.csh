rm -rf INCA_libs irun.*
irun    -sv \
        #-gui \
        -top Tile_MemCore_tb \
        -timescale 1ns/1ps \
        -l run.log \
        -lps_lib_mfile liblist \
        -access +rwc \
        -notimingchecks \
        -ALLOWREDEFINITION \
        -input ../../gls/cmd.tcl pnr.pg.v /tsmc16/TSMCHOME/digital/Front_End/verilog/tcbn16ffcllbwp16p90_100a/tcbn16ffcllbwp16p90_pwr.v /tsmc16/TSMCHOME/digital/Front_End/verilog/tcbn16ffcllbwp16p90pm_100a/tcbn16ffcllbwp16p90pm_pwr.v ../../gls/tb_Tile_MemCore.v 
