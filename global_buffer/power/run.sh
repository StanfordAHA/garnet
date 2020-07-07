#!/usr/bin/env bash
source /cad/modules/tcl/init/sh
module load base prime

mkdir ./reports

/usr/bin/time -v pt_shell -f pts.tcl
