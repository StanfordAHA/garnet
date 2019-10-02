#!/bin/bash

# VERBOSE=true or false
VERBOSE=false
if   [ "$1" == "-v" ] ; then VERBOSE=true;  shift;
elif [ "$1" == "-q" ] ; then VERBOSE=false; shift;
fi

# Little hack
LITTLE=false
if [ "$1" == "--LITTLE" ] ; then LITTLE="$1"; shift; fi


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

##############################################################################
# From the README:
# To Generate Garnet Verilog and put it in the correct folder for synthesis and P&R:
# 
#     Navigate to CGRAGenerator/hardware/tapeout_16
#     Do ./gen_rtl.sh
# 
# Copied gen_rtl.sh contents below...


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
    #   "--- Genesis Is Starting Work On Your Design ---"
    # from being an expandable category in kite log =>
    #   "=== Genesis Is Starting Work On Your Design ==="
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
    w=32; h=16
    if [ "$LITTLE" == "--LITTLE" ] ; then w=4; h=4; fi
    $nobuf python3 garnet.py --width $w --height $h -v --no_sram_stub \
      |& $nobuf sed "$dash_filter" \
      |& $nobuf tee do_gen.log \
      |& filter || exit
    set +x # echo OFF

    # |& $nobuf cat || exit 13

    echo ""
    echo Checking for errors
    grep -i error do_gen.log
    echo ""

#     if ! test -f garnet.v; then
#       echo ERROR oops where is garnet.v
#       exit 13
#     else
#       echo "Now we are here: `pwd`"
#       set -x # echo ON
#       cp garnet.v genesis_verif/garnet.sv
#       cp -r genesis_verif/ tapeout_16/
#       set +x # echo OFF
#     fi
# 
# #     # POP BACK
# #     echo cd tapeout_16/; cd tapeout_16/
# #     echo "Now we are here: `pwd`"
# #     echo ""
