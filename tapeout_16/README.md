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

To Generate Garnet Verilog and put it in the correct folder for synthesis and P&R:
1. Navigate to CGRAGenerator/hardware/tapeout\_16
2. Do `./gen_rtl.sh`

## Block-Level Synthesis:
1. Navigate to garnet/tapeout\_16
2. Ensure that a constraints file called `constraints_<NAME OF BLOCK>.tcl` exists in scripts/   
2. Do `./run_synthesis.csh <NAME OF TILE> <PWR_AWARE (1 or 0)>`      
  a. Memory tile w/ power domains:  `./run_synthesis.csh Tile_MemCore 1`    
  b. PE Tile w/o power domains:  `./run_synthesis.csh Tile_PE 0`
  
## P&R Flow for Tiles:
1. Navigate to garnet/tapeout\_16
2. Do `./run_layout.csh <NAME OF TILE> <PWR_AWARE (1 or 0)>`(this will take some time to complete)      
  a. Memory tile w/ power domains:  `./run_layout.csh Tile_MemCore 1`    
  b. PE Tile w/o power domains:  `./run_layout.csh Tile_PE 0`

## P&R Flow for Top:
1. Navigate to garnet/tapeout\_16/synth/GarnetSOC_pad_frame
2. Type `innovus -stylus` to open the Innovus tool
3. Type `source ../../scripts/top_flow_multi_vt.tcl`

TODO: Finish instructions for top

