#! /bin/tcsh
# Takes in top level design name as argument and
# # runs basic synthesis script
set echo

setenv DESIGN $1
setenv PWR_AWARE $2
if (-d synth/$1) then
  rm -rf synth/$1
endif




# OMG what a brainiac
set errors=1
# while [ condition ]; do commands; done
while ($errors == 1)

  set pkg=NONE; set lib=NONE


  ./run_dc_pe_synth.csh |& tee /tmp/errors && set errors=0
  # /cad/synopsys/syn/P-2019.03/linux64/syn/bin/common_shell_exec: error
  # while loading shared libraries: libmng.so.1: cannot open shared object
  # file: No such file or directory

#   echo
#   '/cad/synopsys/syn/P-2019.03/linux64/syn/bin/common_shell_exec:
#   error while loading shared libraries: libmng.so.1: cannot open
#   shared object file: No such file or directory' \

#     > /tmp/errors

  echo pkg=$pkg
  ls -l /tmp/errors
  cat /tmp/errors
  echo lib=$lib

  # set errors=1
  if ( $errors == 1 ) then
    set lib=`cat /tmp/errors | grep 'shared lib' \
      | sed 's/://g' \
      | sed 's/^.*shared libraries //' | awk 'NR==1 { print $1; exit }'`



    echo lib=$lib


    apt-file search $lib |& tee /tmp/errors
    set pkg=`sed 's/://g' /tmp/errors | awk 'NR==1{print $1}'`

  echo pkg=$pkg
  ls -l /tmp/errors
  cat /tmp/errors
  echo lib=$lib

    if ( $pkg == NONE ) break



    echo apt-get install $pkg
    apt-get install $pkg || exit 13
  endif
  # set errors=0


end


echo foo
set echo









mkdir synth/$1
if ("$DESIGN" == "Tile_PE") then
    ./run_dc_pe_synth.csh
endif

# module load genus
which genus; which innovus

cd synth/$1
if ("$3" == "") then 
    genus -no_gui -legacy_ui -f ../../scripts/synthesize.tcl || exit 13
else
    cp ../../dummy.v .
    genus -no_gui -legacy_ui -f ../../scripts/synthesize_top.tcl || exit 13
endif
cd ../..
