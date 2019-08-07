#!/bin/bash
set -x

##############################################################################
echo "NOTES"
echo "- had to install pip(!) - 'sudo yum install -y python-pip'"
echo "- had to install pip3(!) - 'sudo yum -y install python36-pip'"
echo "- had to install coreir - 'sudo pip3 install coreir'"
echo "- latest problem:"
echo "-- ERROR: Package 'peak' requires a different Python: 3.6.8 not in '>=3.7'"


##############################################################################
# BEGIN
date; pwd; \ls -l


##############################################################################
# Check requirements
# 
# From garnet README:
#   Install CoreIR
#   Garnet only needs the python binding of coreir

function check_pip {
  pkg="$1"; pkg_found=true
  # echo ""
  # echo "Verifying existence of python package '$pkg'..."
  found=`pip3 list | awk '$1=="'$pkg'"{ print "found"}'`
  if [ $found ] ; then 
    echo "  Found package '$pkg'"
  else
    echo "  Cannot find '$pkg'"
    exit 13
  fi
}

set +x
coreir=true
(check_pip coreir) || coreir=false
if [ $coreir == false ]; then
  echo ""; echo "ERROR no coreir, need to do pip3 install"; exit 13
fi

# (check_pip mymodulefoo) || echo NOPE not found mymodulefoo

##############################################################################
# Check requirements
# 
# Also from garnet README:
#   Install python dependencies
#   $ pip install -r requirements.txt  # install python dependencies
#   $ pip install pytest
#   # Note: If you created a virtualenv, reactive it to load the new `pytest`
#   # binary into your path
#   # $ source venv/bin/activate

set +x
packages=`cat ../requirements.txt \
  | sed 's/.*egg=//' \
  | awk '{print $1}'
`
echo Need packages $packages
found_missing=false
for pkg in $packages; do
  (check_pip $pkg) || found_missing=true
done
if [ $found_missing == true ]; then
  echo ""
  echo "  ERROR missing packages, maybe need to do pip3 install -r ../requirements.txt"
  exit 13
fi

# ERROR: Package 'peak' requires a different Python: 3.6.8 not in '>=3.7' :(
v=`python3 -c 'import sys; print(sys.version_info[0]*1000+sys.version_info[1])'`
echo "Found python version $v -- should be at least 3007"
if [ $v -lt 3007 ] ; then
  echo ""; echo "ERROR found python version $v -- should be at least 3007"; exit 13
fi

set -x
##############################################################################
# From the README:
# Before you start, add the following lines to your .cshrc:
# source /cad/modules/tcl/init/csh
# module load base
# module load genesis2
# module load incisive/15.20.022
# module load lc
# module load syn/latest
# module load innovus/latest
# 
# To Generate Garnet Verilog and put it in the correct folder for synthesis and P&R:
# 
#     Navigate to CGRAGenerator/hardware/tapeout_16
#     Do ./gen_rtl.sh

echo '------------------------------------------------------------------------'
echo 'Setup instructions from README'
date; pwd; \ls -l

# Why was it csh? Let's do bash instead why not!
# source /cad/modules/tcl/init/csh
source /cad/modules/tcl/init/bash

module load base
module load genesis2
module load incisive/15.20.022
module load lc
module load syn/latest
module load innovus/latest


# echo '------------------------------------------------------------------------'
# echo 'Oops no magma'
# # From garnet top-level README:
# # Garnet only needs the python binding of coreir, which should be installed via
# # 
# pip install coreir || exit



echo '------------------------------------------------------------------------'
echo 'Original gen_rtl.sh commands'
date; pwd; \ls -l

if [ -d "genesis_verif/" ]; then
  rm -rf genesis_verif
fi
cd ../
pwd
if [ -d "genesis_verif/" ]; then
  rm -rf genesis_verif
fi

# python2? really?? 'cuz that's what 'python' points to on arm7-aha
python3 garnet.py --width 32 --height 16 -v --no_sram_stub || exit

cp garnet.v genesis_verif/garnet.sv

cp -r genesis_verif/ tapeout_16/

cd tapeout_16/

echo '------------------------------------------------------------------------'
echo 'Block-level synthesis'
##############################################################################
# README again
# Block-Level Synthesis:
# 
#     Navigate to CGRAGenerator/hardware/tapeout_16 NOPE
#     Navigate to garnet/tapeout_16
# 
#     Ensure that a constraints file called
#     constraints_<NAME OF BLOCK>.tcl exists in scripts/
# 
#     Do ./run_synthesis.csh <NAME OF Block>
#     a. Memory tile: ./run_synthesis.csh Tile_MemCore
#     b. PE Tile: ./run_synthesis.csh Tile_PE
# 
# Should already be in tapeout16
date; pwd; \ls -l

./run_synthesis.csh Tile_PE  || exit


echo '------------------------------------------------------------------------'
echo 'PNR flow for tiles'
##############################################################################
# README again finally
# P&R Flow for Tiles:
# 
#     Navigate to CGRAGenerator/hardware/tapeout_16
#     Do ./run_layout.csh <NAME OF TILE>(this will take some time to complete)
#     a. Memory tile: ./run_layout.csh Tile_MemCore
#     b. PE Tile: ./run_layout.csh Tile_PE
# 
# Should already be in tapeout16 I think
date; pwd; \ls -l
./run_layout.csh Tile_PE  || exit

##############################################################################
# Done?
date; pwd; \ls -l




##############################################################################
##############################################################################
##############################################################################
# OLD

# function check_pip {
#   pkg="$1"; pkg_found=true
#   echo "Verifying existence of python package '$pkg'..."
# 
  python3 -c "if 1:
    i=0
    try: import $pkg
    except ImportError: i=13
    except: pass
    print(f'exit({i})')
    exit(i)
  " || echo NOPE
# 
#   if [ $pkg_found == true ]; then
#     echo "Found package '$pkg'"
#   else
#     echo ""
#     echo "Cannot find package '$pkg'; you need to do this:"
#     echo "  pip3 install $pkg"
#     echo ""
#     exit 13
#   fi
# }
# 
# set +x
# check_pip coreir || exit 13
# check_pip mymodulefoo || exit 13
# set -x
