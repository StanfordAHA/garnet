#!/bin/bash
if [ -f ../inputs/design.v ]; then
  echo "Using RTL from parent graph"
  mkdir -p outputs
  (cd outputs; ln -s ../../inputs/design.v)
else
  # SystemRDL run
  make -C $GARNET_HOME/global_controller rtl

  while read F  ; do
    echo "Reading design file: $F"
    cat $F >> outputs/design.v
  done <$GARNET_HOME/global_controller/global_controller.filelist
fi
