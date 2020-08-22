#!/usr/bin/env bash
source /cad/modules/tcl/init/sh
module load base pts/latest

mkdir ./reports

/usr/bin/time -v pt_shell -f pts.tcl
