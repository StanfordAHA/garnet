lvs_mem:
	echo "Running MEM lvs"
	./lvs.sh ../synth/Tile_MemCore/pnr.gds ../synth/Tile_MemCore/pnr.lvs.append.v Tile_MemCore

lvs_pe:
	echo "Running PE lvs"
	./lvs.sh ../synth/Tile_PE/pnr.gds ../synth/Tile_PE/pnr.lvs.append.v Tile_PE

v2lvs_top:
	echo "Running top v2lvs"
	./lvs.sh ./GarnetSOC_pad_frame/pnr.lvs.v ./GarnetSOC_pad_frame/pnr.lvs.v GarnetSOC_pad_frame
