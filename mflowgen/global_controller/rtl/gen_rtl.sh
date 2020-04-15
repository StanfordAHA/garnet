#!/bin/bash

# SystemRDL run
make -C $GARNET_HOME/global_controller rtl

while read F  ; do
    echo "Reading design file: $F"
    cat $GARNET_HOME/global_controller/$F >> outputs/design.v
done <$GARNET_HOME/global_controller/global_controller.filelist
