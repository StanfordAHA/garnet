# 10/2019 sr changed "pnr.lvs.append.v" to "pnr.lvs.v"
# TODO/FIXME Figure out what is/was append.v?

lvs_mem:
	echo "Running MEM lvs"
	./lvs.sh ../synth/Tile_MemCore/pnr.gds ../synth/Tile_MemCore/pnr.lvs.v        Tile_MemCore
#PREV 	./lvs.sh ../synth/Tile_MemCore/pnr.gds ../synth/Tile_MemCore/pnr.lvs.append.v Tile_MemCore

lvs_pe:
	echo "Running PE lvs"
	./lvs.sh ../synth/Tile_PE/pnr.gds ../synth/Tile_PE/pnr.lvs.v        Tile_PE
#PREV 	./lvs.sh ../synth/Tile_PE/pnr.gds ../synth/Tile_PE/pnr.lvs.append.v Tile_PE

# Uses latest/greatest just-built verilog
# FIXME seems wrong...shouldn't first arg be a gds tape??
v2lvs_top:
	echo "Running top v2lvs"
	./lvs.sh ./GarnetSOC_pad_frame/pnr.lvs.v ./GarnetSOC_pad_frame/pnr.lvs.v GarnetSOC_pad_frame

# Uses "official" reference verilog; also uses gds tape as first arg
ref_top: srtop
srtop:
	echo "Running top v2lvs"
	./lvs.sh ../synth/ref/final_final.gds ../synth/ref/pnr.final.lvs.v GarnetSOC_pad_frame



