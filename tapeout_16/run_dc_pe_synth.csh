#! /bin/tcsh

# Starts in tapeout directory e.g. "github/garnet/tapeout_16"
echo "$0 starting here: `pwd`"; echo ""

# Takes in top level design name as argument and runs basic synthesis script

if (-d synth/PE) then
  rm -rf synth/PE
  echo ""
  echo "  Found and deleted existing synth dir 'synth/PE'"
endif

mkdir synth/PE; cd synth/PE
# Now we are in synth directory e.g. "github/garnet/tapeout_16/synth/PE"
echo "Now we are here: `pwd`"; echo ""

echo dc_shell -f ../../scripts/dc_synthesize.tcl  -output_log_file dc.log
dc_shell -f ../../scripts/dc_synthesize.tcl  -output_log_file dc.log

# ../../cutmodule.awk PE \
#   < ../../genesis_verif/garnet.sv \
#   > ../../genesis_verif/garnet.no_pe.sv

echo "Now we are here: `pwd`"; echo ""
cd ../..
# Should now be back in tapeout directory e.g. ""github/garnet/tapeout_16"
echo "Now we are here: `pwd`"; echo ""


echo ""; echo "Remove PE module from unified verilog 'garnet.sv'"
set echo
./cutmodule.awk PE \
  < genesis_verif/garnet.sv \
  > genesis_verif/garnet.no_pe.sv \
  || exit 13
mv genesis_verif/garnet.no_pe.sv genesis_verif/garnet.sv
