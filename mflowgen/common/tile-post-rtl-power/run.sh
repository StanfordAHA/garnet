#!/bin/bash

mkdir $tile_id
cd $tile_id
mflowgen run --design ../
make synopsys-ptpx-rtl
cp *synopsys-ptpx-rtl/outputs/power.hier ../outputs/reports/${tile_id}.hier
