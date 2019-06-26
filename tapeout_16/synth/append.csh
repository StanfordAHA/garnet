#!/bin/bash
awk 'NR==FNR {if ($1=="module") print $2}' ./Tile_MemCore/pnr.lvs.v > ./Tile_MemCore/mem_module_list.txt
sed -i '/\<Tile_MemCore\>/d' ./Tile_MemCore/mem_module_list.txt

awk '
NR==FNR { map[$1] = "m_" $1; next }
{
    for (old in map) {
        new = map[old]
        if ($1==old)
            $1 = new
        else if ($1=="module" && $2==old)
            $2 = new
    }
    print
}
' ./Tile_MemCore/mem_module_list.txt ./Tile_MemCore/pnr.lvs.v > ./Tile_MemCore/pnr.lvs.append.v

awk 'NR==FNR {if ($1=="module") print $2}' ./Tile_PE/pnr.lvs.v > ./Tile_PE/pe_module_list.txt
sed -i '/\<Tile_PE\>/d' ./Tile_PE/pe_module_list.txt

awk '
NR==FNR { map[$1] = "p_" $1; next }
{
    for (old in map) {
        new = map[old]
        if ($1==old)
            $1 = new
        else if ($1=="module" && $2==old)
            $2 = new
    }
    print
}
' ./Tile_PE/pe_module_list.txt ./Tile_PE/pnr.lvs.v > ./Tile_PE/pnr.lvs.append.v
