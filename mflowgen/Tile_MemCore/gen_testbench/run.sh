set +x
#pushd .
#cd $GARNET_HOME
#if [ ! -d ./dump ]; then
#    mkdir dump
#fi
#cp tests/test_memory_core/test_memory_core.py .
#python test_memory_core.py
#popd
#cp $GARNET_HOME/dump/Interconnect_tb.sv outputs/testbench.sv
#cp $GARNET_HOME/dump/Interconnect.v outputs/array_rtl.v
set -x
