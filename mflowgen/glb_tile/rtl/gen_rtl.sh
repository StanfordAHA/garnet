#!/bin/bash

# SystemRDL run
$GARNET_HOME/systemRDL/perlpp.pl $GARNET_HOME/global_buffer/systemRDL/rdl_models/glb.rdl -o $GARNET_HOME/global_buffer/systemRDL/rdl_models/glb.rdl.final
java -jar $GARNET_HOME/systemRDL/Ordt.jar -parms $GARNET_HOME/global_buffer/systemRDL/ordt_params/glb.parms -systemverilog $GARNET_HOME/global_buffer/systemRDL/output/ $GARNET_HOME/global_buffer/systemRDL/rdl_models/glb.rdl.final

while read F  ; do
  if [[ "$F" =~ "gl" || "$F" =~ "ifc" ]]; then
    echo "Reading design file: $F"
    cat $GARNET_HOME/global_buffer/rtl/$F >> outputs/design.v
  fi
done <$GARNET_HOME/global_buffer/rtl/global_buffer.filelist
