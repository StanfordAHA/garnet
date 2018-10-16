#!/bin/tcsh
echo "##" > run_synthesis.csh
foreach xfile (`find ../genesis_verif/ -name "pe_tile*.v" -o -name "xmemory_tile*.v"`)
  set file = `echo $xfile | sed 's/..\/genesis_verif\///'` 
  set file = `echo $file | sed 's/\.v//'` 
  echo "if (-d $file) then"  >> run_synthesis.csh
  echo " rm -rf $file" >> run_synthesis.csh
  echo "endif" >> run_synthesis.csh
  echo "mkdir $file" >> run_synthesis.csh
  echo "cd $file" >> run_synthesis.csh
  echo "setenv DESIGN $file" >> run_synthesis.csh
  echo "/cad/cadence/GENUS17.21.000.lnx86/bin/genus -legacy_ui -f ../../scripts/synthesize.tcl" >> run_synthesis.csh
  echo "cd .." >> run_synthesis.csh
  echo "##########" >> run_synthesis.csh
end
