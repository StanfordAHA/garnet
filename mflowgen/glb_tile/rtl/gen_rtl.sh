#!/bin/bash

# SystemRDL run
make -C $GARNET_HOME/global_buffer rtl

while read F  ; do
  if [[ "$F" =~ "gl" || "$F" =~ "ifc" ]]; then
    echo "Reading design file: $F"
    cat $GARNET_HOME/global_buffer/rtl/$F >> outputs/design.v
  fi
done <$GARNET_HOME/global_buffer/rtl/global_buffer.filelist
