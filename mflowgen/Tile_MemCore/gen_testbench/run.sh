# Go to garnet and create the testbench
pushd $GARNET_HOME
if [ ! -d ./dump ]; then
    mkdir dump
fi
cp ./tests/test_memory_core/test_memory_core.py .
python test_memory_core.py --app conv_3_3 --xcelium --tempdir_override
popd

# Now copy outputs out
cp $GARNET_HOME/dump/Interconnect_tb.sv outputs/testbench.sv
cp $GARNET_HOME/dump/Interconnect.v outputs/array_rtl.v
cp /cad/cadence/GENUS17.21.000.lnx86/share/synth/lib/chipware/sim/verilog/CW/CW_fp_mult.v outputs/CW_fp_mult.v
cp /cad/cadence/GENUS17.21.000.lnx86/share/synth/lib/chipware/sim/verilog/CW/CW_fp_add.v outputs/CW_fp_add.v

