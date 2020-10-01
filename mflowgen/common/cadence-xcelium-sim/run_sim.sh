#!/bin/sh

sed -i "1 i\`define CLK_PERIOD ${clock_period}" inputs/testbench.sv

# Default arguments
ARGS="-sv -timescale 1ns/1ns -access +rwc"
ARGS="$ARGS -input inputs/cmd.tcl -ALLOWREDEFINITION"

if [ "$PWR_AWARE" = "True" ]; then
  rm inputs/design.vcs.v
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

# Set-up compiler directive for Tile_MemCore
# Define TSMC_CM_NO_WARNING to avoid following warning:
# Warning tb_Tile_MemCore.dut.MemCore_inst0.LakeTop_W_inst0_LakeTop_mem_0_mem_inst_0_pt_1.CLK_OPERATION : 
#   input CLK unknown/high-Z at simulation time 
# Define TSMC_NO_TESTPINS_DEFAULT_VALUE_CHECK to avoid following error:
#   Error tb_Tile_MemCore.dut.MemCore_inst0.LakeTop_W_inst0_LakeTop_mem_0_mem_inst_0_pt_1 : 
#   input RTSEL should be set to 2'b01 at simulation time    
if [ $design_name == "Tile_MemCore" ]; then
   ARGS="$ARGS +define+TSMC_CM_NO_WARNING +define+TSMC_NO_TESTPINS_DEFAULT_VALUE_CHECK"
fi

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

# Run NC-SIM and print out the command
(
  set -x;
  xrun $ARGS
)
