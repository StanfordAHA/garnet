#!/bin/bash

mkdir build
cd build
mflowgen run --design ../../tile-pe-clock-gate
make synopsys-dc-synthesis
