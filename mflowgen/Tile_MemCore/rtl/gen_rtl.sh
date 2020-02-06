#!/bin/bash
current_dir=$(pwd)
cd $GARNET_HOME
if [ -d "genesis_verif/" ]; then
  rm -rf genesis_verif
fi

python garnet.py  -v --no-sram-stub --no-pd

cp garnet.v genesis_verif/garnet.sv

cat genesis_verif/* >> $current_dir/outputs/design.v
#cp garnet.v $current_dir/outputs/design.v


cd $current_dir
