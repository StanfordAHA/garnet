#!/usr/bin/env bash

# SystemRDL run
make clean
make -C $GARNET_HOME/global_buffer rtl CGRA_WIDTH=${cgra_width} NUM_GLB_TILES=${num_glb_tiles}

rm -f outputs/design.v

while read F  ; do
    echo "Reading design file: $F"
    cat $GARNET_HOME/global_buffer/rtl/$F >> outputs/design.v
done <$GARNET_HOME/global_buffer/rtl/global_buffer.filelist
