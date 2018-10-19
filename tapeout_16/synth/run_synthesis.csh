##
#if (-d pe_tile_new_unq1) then
# rm -rf pe_tile_new_unq1
#endif
#mkdir pe_tile_new_unq1
#cd pe_tile_new_unq1
#setenv DESIGN pe_tile_new_unq1
#/cad/cadence/GENUS17.21.000.lnx86/bin/genus -legacy_ui -f ../../scripts/synthesize.tcl
#innovus -replay ../../scripts/layout_pe_tile_new.tcl
#cd ..
###########
#if (-d memory_tile_unq1) then
# rm -rf memory_tile_unq1
#endif
#mkdir memory_tile_unq1
#cd memory_tile_unq1
#setenv DESIGN memory_tile_unq1
#/cad/cadence/GENUS17.21.000.lnx86/bin/genus -legacy_ui -f ../../scripts/synthesize.tcl
#innovus -replay ../../scripts/layout_memory_tile.tcl
#cd ..
###########
#if (-d top) then
# rm -rf top
#endif
#mkdir top
#cd top
#setenv DESIGN top
#/cad/cadence/GENUS17.21.000.lnx86/bin/genus -legacy_ui -f ../../scripts/synthesize.tcl

if (-d Tile_PECore) then
 rm -rf Tile_PECore
endif
mkdir Tile_PECore
cd Tile_PECore
setenv DESIGN Tile_PECore
/cad/cadence/GENUS17.21.000.lnx86/bin/genus -legacy_ui -f ../../scripts/synthesize.tcl
# innovus -replay ../../scripts/layout_pe_tile_new.tcl
cd ..
