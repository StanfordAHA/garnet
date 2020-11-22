#!/bin/bash

mkdir $tile_id
cd $tile_id
mflowgen run --design ../
make synopsys-ptpx-gl
cp *synopsys-ptpx-gl/outputs/power.hier ../outputs/reports/${tile_id}.hier
