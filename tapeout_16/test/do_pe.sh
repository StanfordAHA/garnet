#!/bin/bash

VERBOSE=true
VERBOSE=false

cd ..
source /cad/modules/tcl/init/bash
module load genesis
module load base
python3 garnet.py --width 32 --height 16 -v --no_sram_stub


exit



# Default =  do it all
do_package_check=true
do_gen=true
do_synthesis=true
do_layout=true

# # Debugging synthesis script
# do_package_check=false
# do_gen=false
# do_synthesis=true
# do_layout=false



# Check to see if we're in the right place
# expr `pwd` : '.*/garnet/tapeout_16$' && rightplace=true || rightplace=false
expr `pwd` : '.*/tapeout_16$' > /dev/null && rightplace=true || rightplace=false
if [ $rightplace != true ] ; then
  echo ""
  echo "ERROR looks like you're in the wrong place"
  echo "- you are here: `pwd`"
  echo "- should be here: .../garnet/tapeout_16"
  exit 13
fi

# # Impatience; do layout only
# do_package_check=false
# do_gen=false
# do_synthesis=false

##############################################################################
if [ $VERBOSE == true ] ; then
    cat test/do_pe.notes.txt
fi

##############################################################################
# Check requirements
# 
# From garnet README:
#   Install CoreIR
#   Garnet only needs the python binding of coreir
# 
# # From garnet top-level README:
# # Garnet only needs the python binding of coreir, which should be installed via
# # 
# pip install coreir || exit

# date; pwd; \ls -lt | head
echo "
do_pe.sh ------------------------------------------
do_pe.sh VERIFY PIP AND PYTHON VERSIONS
do_pe.sh `date` - `pwd`
"

function check_pip {
  pkg="$1"; pkg_found=true
  # echo ""
  # echo "Verifying existence of python package '$pkg'..."
  found=`pip3 list | awk '$1=="'$pkg'"{ print "found"}'`
  if [ $found ] ; then 
    [ $VERBOSE == true ] && echo "  Found package '$pkg'"
    return 0
  else
    echo "  ERROR Cannot find installed python package '$pkg'"
    exit 13
  fi
}

# coreir is one of the packages in requirements.txt so...shouldn't need it here...?
# set +x # no echo
# coreir=true
# (check_pip coreir) || coreir=false
# if [ $coreir == false ]; then
#   echo ""; echo "ERROR no coreir, need to do pip3 install"; exit 13
# fi
# # (check_pip mymodulefoo) || echo NOPE not found mymodulefoo

# Check for python3.7 FIXME I'm sure there's a better way... :(
# ERROR: Package 'peak' requires a different Python: 3.6.8 not in '>=3.7' :(

set +x # no echo / no debug
v=`python3 -c 'import sys; print(sys.version_info[0]*1000+sys.version_info[1])'`
echo "Found python version $v -- should be at least 3007"
if [ $v -lt 3007 ] ; then
  echo ""; echo "ERROR found python version $v -- should be at least 3007"; exit 13
fi

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

echo "
do_pe.sh ------------------------------------------
do_pe.sh VERIFY PYTHON PACKAGE REQUIREMENTS
do_pe.sh `date` - `pwd`
"

# don't do this no mo
# # FIXME oh this is terrible terrible
# [ $BUILDKITE ] && pip3 install -r ../requirements.txt

set +x # no echo
packages=`cat ../requirements.txt \
  | sed 's/.*egg=//' \
  | sed 's/==.*//' \
  | sed 's/buffer_mapping/buffer-mapping/' \
  | sed 's/ordered_set/ordered-set/' \
  | sed 's/cosa/CoSA/' \
  | awk '{print $1}'
`
echo Need packages $packages
if [ $do_package_check == true ] ; then
  found_missing=false
  for pkg in $packages; do
    (check_pip $pkg) || found_missing=true
  done
  if [ $found_missing == true ]; then
    echo ""
    echo "ERROR missing packages, maybe need to do pip3 install -r ../requirements.txt"
    exit 13
  fi
fi
echo Found all packages

set +x # no echo
echo "
do_pe.sh ------------------------------------------
do_pe.sh SETUP-INSTRUCTIONS FROM README
do_pe.sh `date` - `pwd`
"
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

# From Alex .cshrc:
# source /cad/modules/tcl/init/bash
# 
# module load base/1.0
# module load genesis2
# module load incisive/15.20.022
# module load genus/latest
# module load lc
# #module load innovus/17.12.000
# module load syn/latest
# module load dc_shell/latest
# module load calibre/2019.1
# module load icadv/12.30.712
# module load innovus/19.10.000

# I guess buildkite $HOME is still in /var/lib? will that cause trouble?
# echo HOME=$HOME    # HOME=/var/lib/buildkite-agent
# echo USER=$USER    # USER=buildkite-agent

set -x # echo
# To forestall warning : '/home/steveri/.modules' not found
# +(0):WARN:0: Directory '/var/lib/buildkite-agent/.modules' not found
test -f $HOME/.modules || rm    $HOME/.modules # fix your wagon!
test -d $HOME/.modules || mkdir $HOME/.modules
# source /cad/modules/tcl/init/csh # Why was it ever csh??
set +x # no echo sourced crap
source /cad/modules/tcl/init/bash


# module load base
# module load genesis2
# module load incisive/15.20.022
# module load lc
# module load syn/latest
# # module load innovus
set +x # no echo
modules="
  base 
  genesis2 
  incisive/15.20.022
  lc 
  syn/latest
"
for m in $modules; do
  echo module load $m
  module load $m
done

# Maybe don't need this
# # genesis2 is loaded via keyi's pip now, for the docker image anyway
# # otherwise, use module load as before
# [ $BUILDKITE ] || module load genesis2


set +x # no echo
echo "
#
# NOTE `module load genus` loads innovus v17 as a side effect.
# So to get the correct innovus v19, 
# `module load innovus/19.10.000` must happen *after* `module load genus`.
#
"
set -x
/usr/bin/which innovus; /usr/bin/which genus
set +x

echo module load genus;             module load genus
echo module load innovus/19.10.000; module load innovus/19.10.000

set -x
/usr/bin/which innovus; /usr/bin/which genus
set +x

# Should be
#   /cad/cadence/GENUS17.21.000.lnx86/bin/genus
#   /cad/cadence/INNOVUS19.10.000.lnx86/bin/innovus

version_found=`/usr/bin/which innovus`
version_wanted="/cad/cadence/INNOVUS19.10.000.lnx86/bin/innovus"
if [ $version_found != $version_wanted ] ; then
    echo ""
    echo "ERROR innovus version changed"
    echo "- found  '$version_found'"
    echo "- wanted '$version_wanted'"
    exit 13
fi
version_found=`/usr/bin/which genus`
version_wanted="/cad/cadence/GENUS17.21.000.lnx86/bin/genus"
if [ $version_found != $version_wanted ] ; then
    echo ""
    echo "ERROR genus version changed"
    echo "- found  '$version_found'"
    echo "- wanted '$version_wanted'"
    exit 13
fi

##############################################################################
# Need to know that innovus is not throwing errors!!!
set +x # no echo
echo "
do_pe.sh ------------------------------------------
do_pe.sh VERIFYING CLEAN INNOVUS
do_pe.sh `date` - `pwd`
"

echo "innovus -no_gui -execute exit"

if [ $VERBOSE == true ] ; 
  then filter=(stdbuf -oL -eL cat)
  else filter=(stdbuf -oL -eL egrep 'Version|ERROR|Summary')
fi

# It leaves little turds, so use a temp directory
mkdir tmp.$$; cd tmp.$$
  stdbuf -oL -eL innovus -no_gui -execute exit |& stdbuf -oL -eL tee tmp.iout | ${filter[*]}
  grep ERROR tmp.iout > /dev/null && ierr=true || ierr=false
cd ..; /bin/rm -rf tmp.$$
if [ $ierr == true ] ; then
    echo ""
    echo "ERROR looks like innovus install is not clean!"
    exit 13
fi


##############################################################################
# From the README:
# To Generate Garnet Verilog and put it in the correct folder for synthesis and P&R:
# 
#     Navigate to CGRAGenerator/hardware/tapeout_16
#     Do ./gen_rtl.sh
# 
# Copied gen_rtl.sh contents below...
set +x # no echo
if [ $do_gen == true ] ; then
    echo "
    do_pe.sh -------------------------------------------------------------
    do_pe.sh GEN GARNET VERILOG, PUT IT IN CORRECT FOLDER FOR SYNTH/PNR
    do_pe.sh `date` - `pwd`
    " | sed 's/^ *//'
    set -x # echo ON

    if [ -d "genesis_verif/" ]; then rm -rf genesis_verif; fi

    # POP UP
    cd ../; pwd
    if [ -d "genesis_verif/" ]; then rm -rf genesis_verif; fi

    function filter {
      VERBOSE=true
      if [ $VERBOSE == true ] ; 
        then stdbuf -oL -eL cat $1
        else stdbuf -oL -eL egrep 'from\ module|^Running' $1 | stdbuf -oL -eL sed '/^Running/s/ .input.*//'
      fi
    }


    pwd; ls -l


# ERROR: Cannot find library libcoreir-float_DW.so in paths:
#   .
#   /usr/local/lib
#   /usr/lib
#   /cad/cadence/INNOVUS19.10.000.lnx86/tools.lnx86/lib/64bit
#   /cad/cadence/INNOVUS19.10.000.lnx86/share/oa/lib/linux_rhel50_gcc48x_64/opt
#   /cad/common/Linux/x86_64/lib
#   /cad/cadence/INCISIVE15.20.022/tools/lib
#   /cad/cadence/INCISIVE15.20.022/tools/dfII/lib
#   /cad/synopsys/syn/P-2019.03/lib
#  
# /lib/libcoreir.so(_ZN6CoreIR14DynamicLibrary11openLibraryESs+0x231)[0x7f591a565557]
# 
# 
#         magma.compile("garnet", garnet_circ, output="coreir-verilog",
#                       coreir_libs={"float_DW"})







    pip list
    pip show coreir

find /usr/local/lib | grep DW
/usr/local/lib/python3.7/site-packages/coreir/libcoreir-float_DW.so




    stdbuf -oL -eL python3 garnet.py --width 32 --height 16 -v --no_sram_stub \
      |& stdbuf -oL -eL tee do_gen.log \
      |& stdbuf -oL -eL cat || exit 13
#       |& filter || exit

    set -x
    echo Checking for errors
    grep -i error do_gen.log

    pwd; ls -l


    test -f garnet.v || echo ERROR oops where is garnet.v
    test -f garnet.v || exit 13

    cp garnet.v genesis_verif/garnet.sv
    cp -r genesis_verif/ tapeout_16/
    set +x # echo OFF

    # POP BACK
    echo cd tapeout_16/
    cd tapeout_16/
fi


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

set +x # no echo
if [ $do_synthesis == true ] ; then
    set -x
    # date; pwd; \ls -lt | head
    echo "
    do_pe.sh -------------------------------------------------------------
    do_pe.sh BLOCK-LEVEL SYNTHESIS
    do_pe.sh `date` - `pwd`
    do_pe.sh
    " | sed 's/^ *//'
    set -x # echo ON
    nobuf='stdbuf -oL -eL'
    filter=cat # default
    [ $VERBOSE == true ] || filter=./test/run_synthesis.filter
    PWR_AWARE=1
    pwd; ls -ld run*
    $nobuf ./run_synthesis.csh Tile_PE $PWR_AWARE \
      | $nobuf $filter \
      || exit 13
    set +x # echo OFF
fi

set -x


# echo '------------------------------------------------------------------------'
# echo 'PNR flow for tiles'
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
set +x # no echo
if [ $do_layout == true ] ; then
    # date; pwd; \ls -lt | head
    echo "
    do_pe.sh -------------------------------------------------------------
    do_pe.sh PNR FLOW FOR TILES (LAYOUT)
    do_pe.sh `date` - `pwd`
    do_pe.sh
    " | sed 's/^ *//'
    set -x # echo ON
    nobuf='stdbuf -oL -eL'
    filter=cat # default
    [ $VERBOSE == true ] || filter=./test/run_layout.filter
    PWR_AWARE=1
    $nobuf ./run_layout.csh Tile_PE $PWR_AWARE \
      | $nobuf $filter \
      || exit 13
    set +x # echo OFF
fi

# PWR_AWARE=1
# ./run_layout.csh Tile_PE $PWR_AWARE || exit

##############################################################################
# Done?
echo "
do_pe.sh -------------------------------------------------------------
do_pe.sh DONE!
do_pe.sh `date` - `pwd`
do_pe.sh
"
# date; pwd; \ls -lt | head




##############################################################################
##############################################################################
##############################################################################
# OLD

# function check_pip {
#   pkg="$1"; pkg_found=true
#   echo "Verifying existence of python package '$pkg'..."
# 


#   python3 -c "if 1:
#     i=0
#     try: import $pkg
#     except ImportError: i=13
#     except: pass
#     print(f'exit({i})')
#     exit(i)
#   " || echo NOPE


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


##############################################################################
#OLD

## Step 1 - Requirements - https://www.python.org/downloads/ - latest is 3.7.4
# sudo yum install gcc openssl-devel bzip2-devel libffi-devel
# 
## Step 2 - Download Python 3.7
# cd /usr/src
# sudo wget https://www.python.org/ftp/python/3.7.4/Python-3.7.4.tgz
# sudo tar xzf Python-3.7.4.tgz
# 
## Step 3 - Install Python 3.7
# cd Python-3.7.4
# sudo ./configure --enable-optimizations
# # make altinstall is used to prevent replacing the default python binary file /usr/bin/python.)
# # make altinstall
# sudo make install
# 
## Step 4 - Check Python Version
# python -V
# python3 -V
# python3.7 -V
# python2 -V
# 
## Step 5 - clean up
# sudo rm /usr/src/Python-3.7.4.tgz
# sudo mv /usr/src/Python-3.7.4/ /tmp
##############################################################################

# python3 -c 'import sys; print(sys.version_info[0]*1000+sys.version_info[1])' || echo FAIL3
# python3 -c 'import sys; print(sys.version_info)' || echo FAIL3
# python -c 'import sys; print(sys.version_info)' || echo FAIL
# 
# python  -V || echo FAIL
# python2 -V || echo FAIL2
# python3 -V || echo FAIL3


##############################################################################
# set -x
# function filter {
#   # Note, innovus can say "0 errors" in the log even if no errors
#   if [ $VERBOSE == true ] ; 
#     then stdbuf -oL -eL cat $1
#     else stdbuf -oL -eL egrep 'Version|ERROR|Summary' $1
#   fi
# }
# # stdbuf -oL -eL innovus -no_gui -execute exit |& filter | tee $iout
# 
# # It leaves little turds, so use a temp directory
# mkdir tmp.$$; cd tmp.$$
#   iout=/tmp/tmp$$
#   stdbuf -oL -eL innovus -no_gui -execute exit |& stdbuf -oL -eL tee $iout | filter
# cd ..; /bin/rm -rf tmp.$$
# 
# 
# # filter=(stdbuf -oL -eL egrep "Version")
# # echo Version23 | ${filter[*]}
# 
# 
# 
# grep ERROR $iout > /dev/null && ierr=true || ierr=false
# /bin/rm $iout
# if [ $ierr == true ] ; then
#     echo ""
#     echo "ERROR looks like innovus install is not clean!"
#     exit 13
# fi





# set -x
# 
# filter="grep V"
# echo $filter
# echo Version1 | $filter
# 
# filter="stdbuf -oL -eL egrep 'Version|ERROR|Summary'"
# echo $filter
# echo Version2 | $filter
# echo hep
# echo hop
# 
# filter="egrep Version"
# echo $filter
# echo Version3 | $filter
# 
# filter=(stdbuf -oL -eL egrep "Version")
# echo Version23 | ${filter[*]}
# echo $filter
# echo hep
# echo hop
# exit
# 
# foo='ls -l'
# $foo
# 
# set -x
# VERBOSE=true
# VERBOSE=false
# 
#   if [ $VERBOSE == true ] ; 
#     then filter='stdbuf -oL -eL cat'
#     else filter="stdbuf -oL -eL egrep 'Version|ERROR|Summary'"
#   fi
# 
# echo $filter
# echo hay
# echo hoo
# echo Version | $filter
# exit



# m=~/.modules
# # [ $BUILDKITE ] && m=/var/lib/buildkite-agent/.modules
# # [ $BUILDKITE ] && m=/sim/buildkite-agent/.module
# [ $BUILDKITE ] && m=/var/lib/buildkite-agent/.modules

