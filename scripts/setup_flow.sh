rm -rf genesis*
rm -rf tests/build/*

git checkout flow
git pull

pip install --upgrade -r requirements.txt

pip install -e git://github.com/leonardt/fault.git#egg=fault
cd `pip show fault | grep Location | awk '{print $2}'`
git pull
cd -

pip install -e git://github.com/phanrahan/magma.git#egg=magma
cd `pip show magma | grep Location | awk '{print $2}'`
git pull
cd -

pip install -e git://github.com/thofstee/pyverilog.git#egg=pyverilog
cd `pip show pyverilog | grep Location | awk '{print $2}'`
git pull
cd -

python garnet.py --width 32 --height 16 --verilog

mkdir -p tests/build/logs
cd tests/build
ln -s ../../genesis_verif/* .
ln -s ../../garnet.v .
wget https://raw.githubusercontent.com/StanfordAHA/garnet/master/global_buffer/genesis/TS1N16FFCLLSBLVTC2048X64M8SW.sv  # noqa
wget https://raw.githubusercontent.com/StanfordAHA/lassen/master/tests/build/add.v  # noqa
wget https://raw.githubusercontent.com/StanfordAHA/lassen/master/tests/build/mul.v  # noqa
wget https://raw.githubusercontent.com/StanfordAHA/lassen/master/stubs/DW_fp_add.v  # noqa
wget https://raw.githubusercontent.com/StanfordAHA/lassen/master/stubs/DW_fp_mult.v  # noqa
wget https://raw.githubusercontent.com/StanfordAHA/garnet/master/tests/test_memory_core/sram_stub.v  # noqa
wget https://raw.githubusercontent.com/StanfordAHA/garnet/master/tests/AO22D0BWP16P90.sv  # noqa
wget https://raw.githubusercontent.com/StanfordAHA/garnet/master/tests/AN2D0BWP16P90.sv  # noqa
ln -s sram_stub.v sram_512w_16b.v
# TODO might be able to bypass this if we could switch to system_clk without having to do it over jtag...
cp /cad/cadence/GENUS17.21.000.lnx86/share/synth/lib/chipware/sim/verilog/CW/CW_tap.v .
cd -

python tests/test_garnet/_test_flow.py --from-verilog --recompile --width 32
