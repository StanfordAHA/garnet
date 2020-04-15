#!/bin/bash

# SystemRDL run
make -C $GARNET_HOME/global_controller rtl

while read F  ; do
  if [[ "$F" =~ "DW" ]]; then
    echo "Reading design file: $F"
    cat $F >> outputs/design.v
  else
    echo "Reading design file: $F"
    cat $GARNET_HOME/global_controller/$F >> outputs/design.v
  fi
done <$GARNET_HOME/global_controller/global_controller.filelist
