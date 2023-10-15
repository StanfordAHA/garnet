#!/usr/bin/env bash

# Get Current Directory
CUR_DIR=$(pwd)

# Clone the SoC Repo
# git clone https://github.com/StanfordAHA/AhaM3SoC.git aham3soc
cp -r /sim/pohan/aham3soc .

if [ "$WHICH_SOC" == "amber" ]; then
# NOW: to make this branch (master-tsmc) work, must use amber soc
# FIXME/TODO: should be part of top-level parms
# FIXME/TODO: whrere are top-level parms???
amber_soc=83dca39f4e4568ae134f0af69c2ad1b0c8adf6e7
(cd aham3soc; git checkout $amber_soc)

# Clone the ARM IP Repo
git clone git@r7arm-aha:nyengele/aham3soc_armip.git aham3soc_armip
else
# Clone the ARM IP Repo
git clone /sim/repos/aham3soc_armip aham3soc_armip
fi


# Generate Pad Frame
mkdir -p aham3soc_pad_frame
make -C aham3soc/hardware/logical/AhaGarnetSoCPadFrame OUT_DIR=${CUR_DIR}/aham3soc_pad_frame
cd ${CUR_DIR}
cp -L aham3soc_pad_frame/io_file outputs/
cp -L aham3soc_pad_frame/io_pad_placement.tcl outputs/

# Create Outputs
mkdir rtl
mv aham3soc rtl/
mv aham3soc_armip rtl/
mv aham3soc_pad_frame rtl/
cp -r rtl outputs/
cp -r rtl-scripts outputs/
