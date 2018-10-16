# README for backend scripts:

Right now, these instructions will only work on the TSMC16 machine.

Before you start, add the following lines to your .cshrc:  
`source /cad/modules/tcl/init/csh`  
`module load base`  
`module load genesis2`  
`module load incisive/15.20.022`  
`module load lc`  
`module load syn/latest`  
`module load innovus/latest`  

## Synthesis:
TODO

## P&R Flow for PE Tile:
1. Navigate to CGRAGenerator/hardware/tapeout\_16/synth/pe\_tile\_new\_unq1
2. Type `innovus` to open the Innovus tool
3. Type `source ../../scripts/layout_pe_tile_new.tcl` (this will take some time to complete)

After this is complete, type `exit` to exit the Innovus tool.

## P&R Flow for Memory Tile:
1. Navigate to CGRAGenerator/hardware/tapeout\_16/synth/memory\_tile\_unq1
2. Type `innovus` to open the Innovus tool
3. Type `source ../../scripts/layout_memory_tile.tcl` (this will take some time to complete)

After this is complete, type `exit` to exit the Innovus tool.

## P&R Flow for Top:
1. Navigate to CGRAGenerator/hardware/tapeout\_16/synth/top
2. Type `innovus -stylus` to open the Innovus tool
3. Type `source ../../scripts/floorplan.tcl`

TODO: Finish instructions for top

