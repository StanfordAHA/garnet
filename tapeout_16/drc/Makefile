drc_pad_frame:
	./drc.sh ../synth/GarnetSOC_pad_frame/pnr.gds GarnetSOC_pad_frame -nofullchip -noantenna

drc_mem:
	./drc.sh ../synth/Tile_MemCore/pnr.gds Tile_MemCore -nofullchip -noantenna

drc_pe:
	./drc.sh ../synth/Tile_PE/pnr.gds Tile_PE -nofullchip -noantenna

drc_tile_grid:
	./drc.sh ../synth/tile_grid/tile_grid.gds GarnetSOC -nofullchip -noantenna

drc_rdl:
	./drc.sh ../synth/rdl_routing/bumps_routed.gds GarnetSOC_pad_frame -noip -noantenna

calibre_pe_dummy:
	./dummy_util.sh ../synth/Tile_PE/pnr.gds Tile_PE

calibre_mem_dummy:
	./dummy_util.sh ../synth/Tile_MemCore/pnr.gds Tile_MemCore
