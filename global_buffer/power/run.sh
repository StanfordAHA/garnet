#!/usr/bin/env bash
source /cad/modules/tcl/init/sh
module load base pts

/usr/bin/time -v /cad/synopsys/pts/K-2015.12/linux64/syn/bin/pt_shell_exec -r /cad/synopsys/pts/K-2015.12 -f pts.tcl
