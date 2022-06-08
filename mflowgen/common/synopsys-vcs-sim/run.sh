#!/bin/sh

# Add DW IP blocks as includes
cp include inputs/include.v

sed -i "1 i\`define CLK_PERIOD ${clock_period}" inputs/testbench.sv

if [ "$PWR_AWARE" = "True" ]; then
  rm inputs/design.vcs.v
fi

# Default arguments
ARGS="-R -sverilog -timescale=1ns/1ps"
ARGS="$ARGS -hsopt"

# Dump waveform
if [ "$waveform" = "True" ]; then
  ARGS="$ARGS +vcs+dumpvars+outputs/run.vcd"
fi

# ADK for GLS
if [ -d "inputs/adk" ]; then
  ARGS="$ARGS inputs/adk/stdcells.v"
  if [ -f "inputs/adk/stdcells-lvt.v" ]; then
      ARGS="$ARGS inputs/adk/stdcells-lvt.v"
  fi
  if [ -f "inputs/adk/stdcells-ulvt.v" ]; then
      ARGS="$ARGS inputs/adk/stdcells-ulvt.v"
  fi
  if [ $PWR_AWARE == "True" ]; then
    ARGS="$ARGS inputs/adk/stdcells-pm-pwr.v inputs/adk/stdcells-pwr.v"
    if [ -f "inputs/adk/stdcells-lvt-pwr.v" ]; then
        ARGS="$ARGS inputs/adk/stdcells-lvt-pwr.v"
    fi
    if [ -f "inputs/adk/stdcells-ulvt-pwr.v" ]; then
        ARGS="$ARGS inputs/adk/stdcells-ulvt-pwr.v"
    fi
  fi
fi

# Set-up testbench
ARGS="$ARGS -top $testbench_name"

# Grab all design/testbench files
for f in inputs/*.v; do
  [ -e "$f" ] || continue
  ARGS="$ARGS $f"
done

# SRAM power hack for now (files need to read in a specific order)"
if [ $PWR_AWARE == "True" ]; then
  if [[ -f "inputs/sram_pwr.v" ]]; then
    ARGS="$ARGS inputs/sram_pwr.v"
  fi
fi

for f in inputs/*.sv; do
  [ -e "$f" ] || continue
  ARGS="$ARGS $f"
done

# Optional arguments
if [ -f "inputs/design.args" ]; then
  ARGS="$ARGS -file inputs/design.args"
fi

# Link DesignWare
ARGS="$ARGS +incdir+/cad/synopsys/icc/M-2016.12-SP2/dw/sim_ver/"

# Run VCS and print out the command
(
  set -x;
  vcs $ARGS
)
