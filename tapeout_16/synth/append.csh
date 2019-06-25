#! /bin/tcsh
./append.awk p_ < ./Tile_PE/pnr.lvs.v > ./Tile_PE/pnr.lvs.append.v
./append.awk m_ < ./Tile_MemCore/pnr.lvs.v > ./Tile_MemCore/pnr.lvs.append.v
sed -i 's/\<p_Tile_PE\>/Tile_PE/g' ./Tile_PE/pnr.lvs.append.v
sed -i 's/\<m_Tile_MemCore/Tile_MemCore/g' ./Tile_PE/pnr.lvs.append.v
