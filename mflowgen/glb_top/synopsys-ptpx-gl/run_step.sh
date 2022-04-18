#! /bin/bash
mkdir -p reports logs

pt_shell -f ptpx.tcl | tee logs/pt.log
cp reports/${design_name}.power.hier.rpt outputs/power.hier
cp reports/${design_name}.power.cell.rpt outputs/power.cell


for inst in $(echo $instances | sed "s/,/ /g")
do
    python parse_report.py --filename reports/${inst}.power.cell.rpt --instances $(echo $parse_modules | sed "s/,/ /g") --csv reports/${inst}.csv
    python parse_report.py --filename reports/${inst}.power.cell.cn.rpt --instances $(echo $parse_modules | sed "s/,/ /g") --csv reports/${inst}.cn.csv
done

