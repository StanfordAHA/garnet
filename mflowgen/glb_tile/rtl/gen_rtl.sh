#!/bin/bash

# SystemRDL run
make -C $GARNET_HOME/global_buffer rtl

rm -f outputs/design.v

while read F  ; do
  if [[ ! "$F" =~ "TS1N" ]]; then
    echo "Reading design file: $F"
    cat $GARNET_HOME/global_buffer/rtl/$F >> outputs/design.v
  fi
done <$GARNET_HOME/global_buffer/rtl/glb_tile.filelist
