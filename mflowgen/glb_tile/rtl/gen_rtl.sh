#!/bin/bash
# Glb can accept rtl as an input from parent graph
if [ -f ../inputs/design.v ]; then
  echo "Using RTL from parent graph"
  mkdir -p outputs
  (cd outputs; ln -s ../../inputs/design.v)
else
  # SystemRDL run
  make -C $GARNET_HOME/global_buffer rtl
  
  rm -f outputs/design.v
  
  while read F  ; do
      echo "Reading design file: $F"
      cat $GARNET_HOME/global_buffer/rtl/$F >> outputs/design.v
  done <$GARNET_HOME/global_buffer/rtl/glb_tile.filelist
fi
