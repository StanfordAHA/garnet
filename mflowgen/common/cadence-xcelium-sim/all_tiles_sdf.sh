#! /bin/bash

if [ $use_sdf == "True" ]; then

if [ ! -d "sdf_logs" ]; then
  mkdir sdf_logs
fi

# Create lists of each tile type...
if [ -f "inputs/design.vcs.v" ]; then
  cat_file=inputs/design.vcs.v
else
  cat_file=inputs/design.vcs.pg.v
fi
# Put tile instance names in files for python script
cat $cat_file | grep 'Tile_PE Tile' | sed 's/\s\+/,/g' | cut -d, -f3 > sdf_Tile_PE.list
cat $cat_file | grep 'Tile_MemCore Tile' | sed 's/\s\+/,/g' | cut -d, -f3 > sdf_Tile_MemCore.list
# Run script to produce the cadence sdf command file for annotating the separate subinstances before the top
python create_sdf_file.py

fi
