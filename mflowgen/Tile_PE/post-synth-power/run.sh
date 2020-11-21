#!/bin/bash

mkdir $tile_id
cd $tile_id
mflowgen run --design ../
make synopsys-ptpx-synth
cp *synopsys-ptpx-synth/outputs/power.hier ../outputs/reports/${tile_id}.hier
