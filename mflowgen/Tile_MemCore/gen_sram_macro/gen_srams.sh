echo "${num_words}x${word_size}m${mux_size}s" >> config.txt

export MC_HOME=mc/tsn16ffcllhdspsbsram_20131200_130a
export PATH="${PATH}:mc/MC2_2013.12.00.f/bin"
sram_name="ts1n16ffcllsblvtc${num_words}x${word_size}m${mux_size}s_130a"
./mc/tsn16ffcllhdspsbsram_130a.pl -file config.txt -NonBIST -NonSLP -NonDSLP -NonSD -NonBWEB

ln -s ../$sram_name/NLDM/${sram_name}_${corner}.lib outputs/sram_tt.lib
ln -s ../$sram_name/GDSII/${sram_name}_m4xdh.gds outputs/sram.gds
ln -s ../$sram_name/LEF/${sram_name}_m4xdh.lef outputs/sram.lef
ln -s ../$sram_name/VERILOG/${sram_name}_pwr.v outputs/sram_pwr.v
ln -s ../$sram_name/VERILOG/${sram_name}.v outputs/sram.v

cd lib2db/
make
cd ..
