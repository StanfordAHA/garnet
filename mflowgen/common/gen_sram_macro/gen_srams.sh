echo "${num_words}x${word_size}m${mux_size}s" >> config.txt
mc_name=tsn16ffcllhdspsbsram_20131200_130a
export MC_HOME=inputs/adk/mc/${mc_name}
export PATH="${PATH}:inputs/adk/mc/MC2_2013.12.00.f/bin"
sram_name="ts1n16ffcllsblvtc${num_words}x${word_size}m${mux_size}s"
if [ $partial_write == True ]; then
  sram_name+="w"
fi

sram_name+="_130a"

##############################################################################
USE_CACHED=True
if [ $USE_CACHED == True ]; then

    # Mar 2021 Temporary fix to get around expired memory-compiler license
    echo '+++ HACK TIME! Using cached srams...'; set -x

    # Use latest gold build as the cache (if hack were less temporary, would use parm / env var here)
    g=$(cd -P /sim/buildkite-agent/gold; pwd)
    echo "Using gold cache '$g'"

    # Use first sram found in cache, so long as it has the right name (e.g. sram_name='ts1n16ffcllsblvtc2048x64m8sw_130a')
    sram_dir=$(find $g -name ${sram_name} | head -1)
    echo "Using srams found in dir '$sram_dir'"
    cp -rp ${sram_dir} .

    # Done w/hack
    set +x; echo '--- continue...'

else
    cmd="./inputs/adk/mc/${mc_name}/tsn16ffcllhdspsbsram_130a.pl -file config.txt -NonBIST -NonSLP -NonDSLP -NonSD"
    if [ ! $partial_write == True ]; then
        cmd+=" -NonBWEB"
    fi
    eval $cmd
fi

ln -s ../$sram_name/NLDM/${sram_name}_${corner}.lib outputs/sram_tt.lib
ln -s ../$sram_name/NLDM/${sram_name}_${bc_corner}.lib outputs/sram_ff.lib
ln -s ../$sram_name/GDSII/${sram_name}_m4xdh.gds outputs/sram.gds
ln -s ../$sram_name/LEF/${sram_name}_m4xdh.lef outputs/sram.lef
ln -s ../$sram_name/VERILOG/${sram_name}_pwr.v outputs/sram-pwr.v
ln -s ../$sram_name/VERILOG/${sram_name}.v outputs/sram.v
ln -s ../$sram_name/SPICE/${sram_name}.spi outputs/sram.spi

# This builds sram_tt.db
cd lib2db/
make
cd ..

# Emit findable error message and die HERE if SRAMs are missing
sram_exists=True
head outputs/sram_tt.lib > /dev/null || sram_exists=False
if [ $sram_exists == "False" ]; then
    echo "**ERROR Could not build SRAMs...memory compiler error maybe?"
    echo exit 13
fi

echo '--- continue...'

