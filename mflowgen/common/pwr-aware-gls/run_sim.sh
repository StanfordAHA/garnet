#!/bin/sh


# Default arguments
ARGS="-sv -timescale 1ns/1ns -access +rwc -notimingchecks"
ARGS="$ARGS -input cmd.tcl -ALLOWREDEFINITION"

# ADK for GLS
if [ -d "inputs/adk" ]; then
  ARGS="$ARGS inputs/adk/*pwr*.v"
fi

# Set-up testbench
if [ $design_name == "Tile_PE" ]; then 
   ARGS="$ARGS -top tb_Tile_PE"
else
   ARGS="$ARGS -top tb_Tile_MemCore" 
fi

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

for f in inputs/*.sv; do
  [ -e "$f" ] || continue
  ARGS="$ARGS $f"
done

for f in *.v; do
  [ -e "$f" ] || continue
  ARGS="$ARGS $f"
done

# Run NC-SIM and print out the command
(
  set -x;
  irun $ARGS
)
