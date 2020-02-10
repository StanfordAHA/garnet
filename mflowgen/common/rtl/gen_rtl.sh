#!/bin/bash
current_dir=$(pwd)
cd $GARNET_HOME
if [ -d "genesis_verif/" ]; then
  rm -rf genesis_verif
fi

cmd="python garnet.py --width $array_width --height $array_height -v --no-sram-stub --no-pd"

if [ $interconnect_only == True ]; then
 cmd+=" --interconnect-only"
fi

eval $cmd

# If there are any genesis files, we need to cat those
# with the magma generated garnet.v
if [ -d "genesis_verif" ]; then
  cp garnet.v genesis_verif/garnet.sv
  cat genesis_verif/* >> $current_dir/outputs/design.v
# Otherwise, garnet.v contains all rtl
else
  cp garnet.v $current_dir/outputs/design.v
fi


cd $current_dir
