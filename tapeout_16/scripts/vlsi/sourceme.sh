source /tools/flexlm/flexlm.sh
export RISCV=/tools/projects/zhemao/craft2-chip/install
export PATH=$PATH:$RISCV/bin

export LD_LIBRARY_PATH=~rigge/gcc/lib64:~rigge/gcc/lib:$LD_LIBRARY_PATH
export LD_LIBRARY_PATH=$RISCV/lib64:$RISCV/lib:$LD_LIBRARY_PATH

# synopsys vcs, also for dve
export PATH=/tools/synopsys/vcs/J-2014.12-SP1/bin:$PATH
export VCS_HOME=/tools/synopsys/vcs/J-2014.12-SP1/
export VCS_64=1

# memory compiler
export INTERRAD_LICENSE_FILE=/tools/commercial/interra/flexlm/license_N28.dat
export TSMCHOME=/tools/tstech16/CLN16FFC/TSMCHOME

# temporary, hopefully
export MC2_INSTALL_DIR=~stevo.bailey/mc2/MC2_2013.12.00.f

export PATH=$PATH:$MC2_INSTALL_DIR/bin

# cadence incisive
export IUSHOME=/tools/cadence/INCISIV/INCISIVE152
export PATH=$IUSHOME/tools/bin:$PATH

# get the right gcc 
source /opt/rh/devtoolset-2/enable

alias viewgds="calibredrv -dl /users/stevo.bailey/TSMC16.layerprops -s /users/bmzimmer/.calibrewb_workspace/wbinit.tcl -m "

# cadence tools
export PATH=$PATH:/tools/cadence/INNOVUS/INNOVUS162_ISR2/tools/bin:/tools/cadence/GENUS/GENUS162_ISR2/tools/bin:/tools/cadence/INCISIV/INCISIVE152/tools/bin

# calibre (DRC/LVS)
export MGC_HOME=/tools/mentor/calibre/aoi_cal_2016.4_15.11
export PATH=$PATH:$MGC_HOME/bin

# Quantus PVS/QRC
export PVS_HOME=/tools/cadence/PVS/PVS151 # [stevo]: just in case
export PVSHOME=/tools/cadence/PVS/PVS151
export PATH=$PATH:$PVSHOME/tools/bin
export QRC_HOME=/tools/cadence/EXT/EXT151
export PATH=$PATH:$QRC_HOME/tools/bin

