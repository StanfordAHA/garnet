#! /bin/bash
mkdir -p reports logs

pt_shell -f ptpx.tcl | tee logs/pt.log
cp reports/${design_name}.power.hier.rpt outputs/power.hier
cp reports/${design_name}.power.cell.rpt outputs/power.cell
