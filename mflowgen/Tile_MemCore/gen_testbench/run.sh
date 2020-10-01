set +x
pushd $GARNET_HOME

if [ ! -d ./dump ]; then
    mkdir dump
fi

pushd dump
cp /cad/cadence/GENUS17.21.000.lnx86/share/synth/lib/chipware/sim/verilog/CW/CW_fp_mult.v ./
cp /cad/cadence/GENUS17.21.000.lnx86/share/synth/lib/chipware/sim/verilog/CW/CW_fp_add.v ./
popd

cp ./tests/test_memory_core/test_memory_core.py .
python test_memory_core.py
popd
cp $GARNET_HOME/dump/Interconnect_tb.sv outputs/testbench.sv
cp $GARNET_HOME/dump/Interconnect.v outputs/array_rtl.v
set -x
