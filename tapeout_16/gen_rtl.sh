#!/bin/bash
if [ -d "genesis_verif/" ]; then
  rm -rf genesis_verif
fi
cd ../
if [ -d "genesis_verif/" ]; then
  rm -rf genesis_verif
fi

python garnet.py --width 32 --height 16 -v --no_sram_stub

cp garnet.v genesis_verif/garnet.sv

cp -r genesis_verif/ tapeout_16/

cd tapeout_16/
