setenv DESIGN Tile_PECore
dc_shell -o Tile_PECore_syn.log -f ../scripts/synthesize.tcl

setenv DESIGN Tile_MemCore
dc_shell -o Tile_MemCore_syn.log -f ../scripts/synthesize.tcl
