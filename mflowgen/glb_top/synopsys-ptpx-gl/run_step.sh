#! /bin/bash
mkdir -p reports logs

# Quick fix because synopsys requires backslash as an escape key for bracket
sed -i 's/\[/\\\[/' inputs/run.saif
sed -i 's/\]/\\\]/' inputs/run.saif
sed -i 's/\\\\/\\/' inputs/run.saif

pt_shell -f ptpx.tcl | tee logs/pt.log
cp reports/${design_name}.power.hier.rpt outputs/power.hier
cp reports/${design_name}.power.cell.rpt outputs/power.cell
