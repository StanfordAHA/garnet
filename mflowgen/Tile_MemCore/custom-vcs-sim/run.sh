#!/bin/sh

# Default arguments
ARGS="-R -sverilog -timescale=1ns/1ps"
ARGS="$ARGS -hsopt"

# Dump waveform
if [ "$waveform" = "True" ]; then
# For me it is a vcd because my version of vcs doesn't recognize the vpd system tasks?
    ARGS="$ARGS +vcs+dumpvars+outputs/design.vcd"
fi

# ADK for GLS
if [ -d "inputs/adk" ]; then
    ARGS="$ARGS inputs/adk/stdcells.v inputs/adk/stdcells-lvt.v inputs/adk/stdcells-ulvt.v"
fi

# Set-up testbench
ARGS="$ARGS -top $testbench_name"

# Grab all design/testbench files
for f in inputs/*.v; do
    [ -e "$f" ] || continue
    ARGS="$ARGS $f"
done

for f in inputs/*.sv; do
    [ -e "$f" ] || continue
    ARGS="$ARGS $f"
done

# Optional arguments
if [ -f "inputs/design.args" ]; then
    ARGS="$ARGS -file inputs/design.args"
fi

# Run VCS and print out the command
(
    set -x;
    vcs $ARGS
)

# Now convert to saif for ptpx-gl
vcd2saif -input outputs/design.vcd -output outputs/run.saif
