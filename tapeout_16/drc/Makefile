drc_pad_frame:
	./drc.sh ../synth/GarnetSOC_pad_frame/pnr.gds GarnetSOC_pad_frame -nofullchip -noantenna

drc_pe:
	./drc.sh ../synth/Tile_PE/pnr.gds Tile_PE -nofullchip -noantenna

drc_density_pe: pe_dummy
	./drc.sh ./Tile_PE_with_dummy.gds Tile_PE -nofullchip -noantenna

drc_mem:
	./drc.sh ../synth/Tile_MemCore/pnr.gds Tile_MemCore -nofullchip -noantenna

drc_density_mem: mem_dummy
	./drc.sh ./Tile_MemCore_with_dummy.gds Tile_MemCore -nofullchip -noantenna

antenna_mem:
	./drc.sh ../synth/Tile_MemCore/pnr.gds Tile_MemCore -noip -nofullchip

antenna_pe:
	./drc.sh ../synth/Tile_PE/pnr.gds Tile_PE -noip -nofullchip

drc_tile_grid:
	./drc.sh ../synth/tile_grid/tile_grid.gds GarnetSOC -nofullchip -noantenna

drc_rdl:
	./drc.sh ../synth/rdl_routing/bumps_routed.gds GarnetSOC_pad_frame -noip -noantenna

pe_dummy:
	./dummy_util.sh ../synth/Tile_PE/pnr.gds Tile_PE

mem_dummy:
	./dummy_util.sh ../synth/Tile_MemCore/pnr.gds Tile_MemCore

fullchip_dummy:
	./dummy_util.sh ../synth/GarnetSOC_pad_frame/final.gds GarnetSOC_pad_frame
