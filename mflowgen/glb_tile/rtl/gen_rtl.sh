#!/bin/bash

# SystemRDL run
java -jar $GARNET_HOME/systemRDL/Ordt.jar -parms $GARNET_HOME/global_buffer/systemRDL/ordt_params/glb.parms -systemverilog $GARNET_HOME/global_buffer/systemRDL/output/ $GARNET_HOME/global_buffer/systemRDL/rdl_models/glb.rdl
cp $GARNET_HOME/global_buffer/systemRDL/output/{glb_jrdl_logic.sv,glb_jrdl_decode.sv,glb_pio.sv} $GARNET_HOME/global_buffer/rtl/

while read F  ; do
  if [[ "$F" =~ "gl" || "$F" =~ "ifc" ]]; then
    echo "Reading design file: $F"
    cat $GARNET_HOME/global_buffer/rtl/$F >> outputs/design.v
  fi
done <$GARNET_HOME/global_buffer/rtl/global_buffer.filelist
