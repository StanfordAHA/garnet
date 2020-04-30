#!/usr/bin/env bash

step_dir=$(pwd)
mkdir filelists

###############################################################################
#                   Generate Garnet File List                                 #
###############################################################################
cd $GARNET_HOME
if [ -d "genesis_verif/" ]; then
  rm -rf genesis_verif
fi

cmd="python garnet.py --width $array_width --height $array_height -v --no-sram-stub --no-pd"

if [ $interconnect_only == True ]; then
 cmd+=" --interconnect-only"
fi

eval $cmd


# Put everything in genesis_verif and create file list
mkdir -p genesis_verif
cp garnet.v genesis_verif/garnet.sv

SV_FILES=$( find -L genesis_verif -type f -name '*.sv' | xargs readlink -f )
V_FILES=$( find -L genesis_verif -type f -name '*.v' | xargs readlink -f )
ALL_FILES=( ${SV_FILES[*]} ${V_FILES[*]} )

for F in ${ALL_FILES[@]}
do
  echo "-v ${F}" >> $step_dir/filelists/garnet.list
done

###############################################################################
#                   Generate GLB File List                                    #
###############################################################################
cd $GARNET_HOME/global_buffer
make rtl
cd rtl
while read F
do
  readlink -f $F | xargs echo >> $step_dir/filelists/glb.list
done<$GARNET_HOME/global_buffer/rtl/global_buffer.filelist

###############################################################################
#                   Generate GLC File List                                    #
###############################################################################
cd $GARNET_HOME/global_controller
make rtl

while read F
do
  readlink -f $F | xargs echo >> $step_dir/filelists/glc.list
done<$GARNET_HOME/global_controller/global_controller.filelist

cd $step_dir
mv filelists outputs/
