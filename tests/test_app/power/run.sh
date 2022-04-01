#!/usr/bin/env bash
export reports=0
export chkpt=0
mkdir -p logs
mkdir -p reports
pt_shell -f ptpx.tcl | tee logs/pt.log 

