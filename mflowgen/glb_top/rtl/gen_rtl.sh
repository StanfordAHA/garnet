#!/bin/bash

# SystemRDL run
make -C $GARNET_HOME/global_buffer rtl

rm -f outputs/design.v

while read F  ; do
    echo "Reading design file: $F"
    cat $GARNET_HOME/global_buffer/rtl/$F >> outputs/design.v
done <$GARNET_HOME/global_buffer/rtl/global_buffer.filelist
