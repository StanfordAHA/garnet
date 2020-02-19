#!/bin/bash

cp /sim/steveri/pad_frame/barebones/pad_frame.sv outputs/design.v
cp /sim/steveri/pad_frame/barebones/io_file outputs/io_file

# Original Tile_MemCore code
# while read F  ; do
#   if [[ "$F" =~ "gl" ]]; then
#     echo "Reading design file: $F"
#     cat $GARNET_HOME/global_buffer/rtl/$F >> outputs/design.v
#   fi
# done <$GARNET_HOME/global_buffer/rtl/global_buffer.filelist

