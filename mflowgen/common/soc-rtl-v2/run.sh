#!/usr/bin/env bash

# Get Current Directory
CUR_DIR=$(pwd)

# Clone the SoC Repo
git clone https://github.com/StanfordAHA/AhaM3SoC.git aham3soc

# Clone the ARM IP Repo
git clone git@r7arm-aha:nyengele/aham3soc_armip.git aham3soc_armip

# Generate Pad Frame
mkdir -p aham3soc_pad_frame
make -C aham3soc/hardware/logical/AhaGarnetSoCPadFrame OUT_DIR=${CUR_DIR}/aham3soc_pad_frame
cd ${CUR_DIR}
cp -L aham3soc_pad_frame/io_file outputs/

# Create Outputs
mkdir rtl
mv aham3soc rtl/
mv aham3soc_armip rtl/
mv aham3soc_pad_frame rtl/
cp -r rtl outputs/
cp -r rtl-scripts outputs/
