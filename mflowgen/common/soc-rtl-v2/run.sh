#!/usr/bin/env bash

# Get Current Directory
CUR_DIR=$(pwd)

# Clone the SoC Repo
cp -r /sim/$(whoami)/zircon/aham3soc .
cp -r /sim/$(whoami)/zircon/aham3soc_armip .

# Generate Pad Frame
mkdir -p aham3soc_pad_frame
make python -C aham3soc/hardware/logical/AhaGarnetSoCPadFrame OUT_DIR=${CUR_DIR}/aham3soc_pad_frame
cd ${CUR_DIR}
cp -L aham3soc_pad_frame/io_pad_placement.tcl outputs/

# Create Outputs
mkdir rtl
mv aham3soc rtl/
mv aham3soc_armip rtl/
mv aham3soc_pad_frame rtl/
cp -r rtl outputs/
cp -r rtl-scripts outputs/
