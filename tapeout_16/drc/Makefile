calibre_pad_frame:
	./drc.sh ~/gds_files/pads_placed.gds GarnetSOC_pad_frame -nofullchip -noantenna

calibre_mem_tile:
	./drc.sh ../synth/Tile_MemCore/pnr.gds Tile_MemCore -nofullchip -noantenna

calibre_pe_tile:
	./drc.sh ../synth/Tile_PE/pnr.gds Tile_PE -nofullchip -noantenna

calibre_tile_grid:
	./drc.sh ../synth/tile_grid/tile_grid.gds GarnetSOC -nofullchip -noantenna

calibre_rdl:
	./drc.sh ../synth/rdl_routing/bumps_routed.gds GarnetSOC_pad_frame -noip -noantenna

calibre_pe_dummy:
	./dummy_util.sh ../synth/Tile_PE/pnr.gds Tile_PE

calibre_mem_dummy:
	./dummy_util.sh ../synth/Tile_MemCore/pnr.gds Tile_MemCore
