#!/bin/bash
./cutmodule.awk Tile_PE < ./genesis_verif/garnet.sv > ./genesis_verif/garnet.no_petile.sv
./cutmodule.awk Tile_MemCore < ./genesis_verif/garnet.no_petile.sv > ./genesis_verif/garnet.no_tiles.sv

rm genesis_verif/garnet.no_petile.sv
mv genesis_verif/garnet.no_tiles.sv genesis_verif/garnet.sv
