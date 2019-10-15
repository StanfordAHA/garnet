#! /usr/bin/env csh
###########
#if (-d top) then
# rm -rf top
#endif
#mkdir top
#cd top
#setenv DESIGN top
#/cad/cadence/GENUS17.21.000.lnx86/bin/genus -legacy_ui -f ../../scripts/synthesize.tcl

setenv PWR_AWARE 1

if (-d Tile_PECore) then
 rm -rf Tile_PECore
endif
mkdir Tile_PECore
cd Tile_PECore
setenv DESIGN Tile_PECore
/cad/cadence/GENUS17.21.000.lnx86/bin/genus -legacy_ui -f ../../scripts/synthesize.tcl
innovus -replay ../../scripts/layout_Tile_PECore.tcl
cd ..


if (-d Tile_MemCore) then
 rm -rf Tile_MemCore
endif
mkdir Tile_MemCore
cd Tile_MemCore
setenv DESIGN Tile_MemCore
/cad/cadence/GENUS17.21.000.lnx86/bin/genus -legacy_ui -f ../../scripts/synthesize.tcl
innovus -replay ../../scripts/layout_Tile_MemCore.tcl
cd ..

