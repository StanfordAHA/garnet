#!/bin/bash

VERBOSE=true
VERBOSE=false

# Default =  do it all
do_package_check=true
do_gen=true
do_synthesis=true
do_layout=true

# Check to see if we're in the right place e.g. "tapeout_16" directory
# expr `pwd` : '.*/garnet/tapeout_16$' && rightplace=true || rightplace=false
expr `pwd` : '.*/tapeout_16$' > /dev/null && rightplace=true || rightplace=false
if [ $rightplace != true ] ; then
  echo ""
  echo "ERROR looks like you're in the wrong place"
  echo "- you are here:   `pwd`"
  echo "- should be here: .../tapeout_16"
  exit 13
fi

# buildkite log: Group and collapse your build output by echoing
# --- [group name] in your build output:
#     echo "--- A section of the build"
# If you want to have the group open by default, use +++ instead of ---:
#     echo "+++ A section of the build"
# echo -e "+++ Running \033[33mspecs\033[0m :cow::bell:"
# 
function header {
  # E.g. "header --- header message" => "--- 07:52 header message"
  pfx=$1; shift
  echo "$pfx `date +%H:%M` $*"
}

##############################################################################
if [ $VERBOSE == true ] ; then
    header --- notes
    cat test/do_pe.notes.txt
fi

# Optional sanity checks
if [ $do_package_check == true ] ; then

  ##############################################################################
  header +++ VERIFY PYTHON VERSION AND PACKAGES

  # Check for python3.7 FIXME I'm sure there's a better way... :(
  # ERROR: Package 'peak' requires a different Python: 3.6.8 not in '>=3.7' :(
  v=`python3 -c 'import sys; print(sys.version_info[0]*1000+sys.version_info[1])'`
  echo "Found python version $v -- should be at least 3007"
  if [ $v -lt 3007 ] ; then
    echo ""; echo "ERROR found python version $v -- should be 3007"; exit 13
  fi
  echo ""

  header +++ VERIFY PYTHON PACKAGE REQUIREMENTS
  ##############################################################################
  # Check requirements
  # From garnet README:
  #   Install python dependencies
  #   $ pip install -r requirements.txt  # install python dependencies
  if [ $VERBOSE == true ];
    then test/requirements_check.sh -v || exit 13
    else test/requirements_check.sh -q || exit 13
  fi
  echo ""
fi

# set +x # no echo
##############################################################################
header +++ MODULE LOAD REQUIREMENTS
source test/module_loads.sh -v
echo ""


##############################################################################
# Need to know that innovus is not throwing errors!!!
header +++ VERIFYING CLEAN INNOVUS
echo ""; 
echo "innovus -no_gui -execute exit"
nobuf='stdbuf -oL -eL'
if [ $VERBOSE == true ] ; 
  then filter=($nobuf cat)
  else filter=($nobuf egrep 'Version|ERROR|Summary')
fi

# It leaves little turds, so use a temp directory
mkdir tmp.$$; cd tmp.$$
  $nobuf innovus -no_gui -execute exit |& $nobuf tee tmp.iout | ${filter[*]}
  grep ERROR tmp.iout > /dev/null && ierr=true || ierr=false
cd ..; /bin/rm -rf tmp.$$
if [ $ierr == true ] ; then
    echo ""
    echo "ERROR looks like innovus install is not clean!"
    exit 13
fi



header --- GENERATE GARNET VERILOG, PUT IT IN CORRECT FOLDER FOR SYNTH/PNR
##############################################################################
# From the README:
# To Generate Garnet Verilog and put it in the correct folder for synthesis and P&R:
# 
#     Navigate to CGRAGenerator/hardware/tapeout_16
#     Do ./gen_rtl.sh
# 
# Copied gen_rtl.sh contents below...
# echo -e "--- generate"
set +x # no echo
if [ $do_gen != true ] ; then
    echo "Skipping generation phase b/c do_gen variable not 'true'"
    echo ""
else
    set +x # echo OFF
    if [ -d "genesis_verif/" ]; then
        "Found (and deleted) existing verilog `pwd`/genesis_verif/"
        rm -rf genesis_verif
    fi
    cd ../; echo "Now we are here: `pwd`"
    if [ -d "genesis_verif/" ]; then
        "Found (and deleted) existing verilog `pwd`/genesis_verif/"
        rm -rf genesis_verif
    fi

    echo ""
    echo "OMG are you kidding me."
    echo "coreir only works if /usr/local/bin comes before /usr/bin."
    echo 'export PATH=/usr/local/bin:$PATH'
    echo ""
    export PATH=/usr/local/bin:$PATH

    # This filter keeps Genesis output
    # "--- Genesis Is Starting Work On Your Design ---"
    # from being an expandable category in kite log =>
    # "=== Genesis Is Starting Work On Your Design ==="
    dash_filter='s/^--- /=== /;s/ ---$/ ===/'

    nobuf='stdbuf -oL -eL'
    function filter {
      set +x # echo OFF
      VERBOSE=true
      if [ $VERBOSE == true ] ; 
        then $nobuf cat $1
        else $nobuf egrep 'from\ module|^Running' $1 \
           | $nobuf sed '/^Running/s/ .input.*//'
      fi
    }

    ##############################################################################
    # THE MAIN EVENT - generation
    set -x # echo ON
    $nobuf python3 garnet.py --width 32 --height 16 -v --no_sram_stub \
      |& $nobuf sed "$dash_filter" \
      |& $nobuf tee do_gen.log \
      |& filter || exit
    set +x # echo OFF

    # |& $nobuf cat || exit 13

    echo ""
    echo Checking for errors
    grep -i error do_gen.log
    echo ""

    if ! test -f garnet.v; then
      echo ERROR oops where is garnet.v
      exit 13
    else
      echo "Now we are here: `pwd`"
      set -x # echo ON
      cp garnet.v genesis_verif/garnet.sv
      cp -r genesis_verif/ tapeout_16/
      set +x # echo OFF
    fi

    # POP BACK
    echo cd tapeout_16/; cd tapeout_16/
    echo "Now we are here: `pwd`"
    echo ""
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

# echo -e "+++ Running \033[33mspecs\033[0m :cow::bell:"
echo -e "--- synthesis"

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
# echo -e "+++ Running \033[33mspecs\033[0m :cow::bell:"
echo -e "--- layout"

echo "ERROR/FIXME SHOULD NOT HAVE TO DO THIS!!!"
echo "ERROR/FIXME below symlink should maybe prevent the following error:
preventing **ERROR: (IMPSE-110): File
  '/sim/ajcars/garnet/tapeout_16/scripts/layout_Tile.tcl' line 64:
  grep: ../Tile_MemCore/results_syn/final_area.rpt: No such file or
  directory.
"
set -x
ls -l synth/Tile_MemCore/results_syn/final_area.rpt || echo not found
if ! test -d synth/Tile_MemCore ; then
  t16synth=/sim/ajcars/aha-arm-soc-june-2019/components/cgra/garnet/tapeout_16/synth
  pwd
  cd synth
    ln -s $t16synth/Tile_MemCore
    pwd
    ls -l $t16synth/Tile_MemCore Tile_MemCore
  cd ..
  pwd
fi
ls -l synth/Tile_MemCore/results_syn/final_area.rpt || echo not found
set +x


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



# cd ..
# source /cad/modules/tcl/init/bash
# module load base
# module load genesis2
# pip show coreir
# set -x
# # python3 garnet.py --width 32 --height 16 -v --no_sram_stub
# python3 garnet.py --width 4 --height 4 -v --no_sram_stub
# exit


# set -x
# echo USER=$USER
# # echo HOME=$HOME    # HOME=/var/lib/buildkite-agent
# # echo USER=$USER    # USER=buildkite-agent
# 
# 
# set -x
# groups
# ls -ld /tsmc16
# ls -ld /tsmc16/TSMCHOME/digital/Front_End/timing_power_noise/NLDM
# ls -l /tsmc16/TSMCHOME/digital/Front_End/timing_power_noise/NLDM/tcbn16ffcllbwp16p90_100a/tcbn16ffcllbwp16p90ssgnp0p72vm40c.lib
# 
# # if [[ $? -ne 0 ]]; then
# #   echo "FAIL"
# #   exit 13
# # fi


# echo "
# do_pe.sh ------------------------------------------
# do_pe.sh VERIFY PIP AND PYTHON VERSIONS
# do_pe.sh `date` - `pwd`
# "

# coreir is one of the packages in requirements.txt so...shouldn't need it here...?
# set +x # no echo
# coreir=true
# (check_pip coreir) || coreir=false
# if [ $coreir == false ]; then
#   echo ""; echo "ERROR no coreir, need to do pip3 install"; exit 13
# fi
# # (check_pip mymodulefoo) || echo NOPE not found mymodulefoo

# echo "
# do_pe.sh ------------------------------------------
# do_pe.sh VERIFY PYTHON PACKAGE REQUIREMENTS
# do_pe.sh `date` - `pwd`
# "

# don't do this no mo
# # FIXME oh this is terrible terrible
# [ $BUILDKITE ] && pip3 install -r ../requirements.txt

# echo "
# do_pe.sh ------------------------------------------
# do_pe.sh SETUP-INSTRUCTIONS FROM README
# do_pe.sh `date` - `pwd`
# "

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

# Maybe don't need this
# # genesis2 is loaded via keyi's pip now, for the docker image anyway
# # otherwise, use module load as before
# [ $BUILDKITE ] || module load genesis2

# echo "
# do_pe.sh ------------------------------------------
# do_pe.sh VERIFYING CLEAN INNOVUS
# do_pe.sh `date` - `pwd`

# 
#   if [ $VERBOSE == true ];
#     then arm_module_loads.sh -v || exit 13
#     else arm_module_loads.sh -q || exit 13
#   fi

#     echo "
#     do_pe.sh -------------------------------------------------------------
#     do_pe.sh GEN GARNET VERILOG, PUT IT IN CORRECT FOLDER FOR SYNTH/PNR
#     do_pe.sh `date` - `pwd`
#     " | sed 's/^ *//'
