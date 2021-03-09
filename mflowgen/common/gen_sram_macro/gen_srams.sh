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

    # Mar 2021 Temporary(?) fix for expired memory-compiler license

    echo '+++ HACK TIME! Using cached srams...'
    set -x

    # E.g. this_dir=/build/gold.223/full_chip/13-gen_sram_macro
    this_dir=`pwd`
    echo this_dir=$this_dir

    # E.g. tail=full_chip/13-gen_sram_macro
    tail=`echo $this_dir | sed 's/^.*full_chip/full_chip/'`
    echo tail=$tail

    # E.g. GOLD=/build/gold.219/full_chip/13-gen_sram_macro
    GOLD=$(cd /sim/buildkite-agent/gold; pwd)
    GOLD=$GOLD/$tail
    echo GOLD=$GOLD

    cd outputs
        ln -s $GOLD/outputs/sram_tt.lib
        ln -s $GOLD/outputs/sram_ff.lib
        ln -s $GOLD/outputs/sram.gds
        ln -s $GOLD/outputs/sram.lef
        ln -s $GOLD/outputs/sram-pwr.v
        ln -s $GOLD/outputs/sram.v
        ln -s $GOLD/outputs/sram.spi
        # Not sure why this one is copied, just mimicking what I see in the cache...
        cp -p $GOLD/outputs/sram_tt.db .
    cd ..
    mv lib2db lib2db.orig
    ln -s $GOLD/lib2db

    set +x
    echo '--- continue...'

else
    cmd="./inputs/adk/mc/${mc_name}/tsn16ffcllhdspsbsram_130a.pl -file config.txt -NonBIST -NonSLP -NonDSLP -NonSD"
    if [ ! $partial_write == True ]; then
        cmd+=" -NonBWEB"
    fi
    eval $cmd

    ln -s ../$sram_name/NLDM/${sram_name}_${corner}.lib outputs/sram_tt.lib
    ln -s ../$sram_name/NLDM/${sram_name}_${bc_corner}.lib outputs/sram_ff.lib
    ln -s ../$sram_name/GDSII/${sram_name}_m4xdh.gds outputs/sram.gds
    ln -s ../$sram_name/LEF/${sram_name}_m4xdh.lef outputs/sram.lef
    ln -s ../$sram_name/VERILOG/${sram_name}_pwr.v outputs/sram-pwr.v
    ln -s ../$sram_name/VERILOG/${sram_name}.v outputs/sram.v
    ln -s ../$sram_name/SPICE/${sram_name}.spi outputs/sram.spi

    cd lib2db/
    make
    cd ..
fi

# Emit findable error message and die HERE if SRAMs are missing
sram_exists=True
head outputs/sram_tt.lib > /dev/null || sram_exists=False
if [ $sram_exists == "False" ]; then
    echo "**ERROR Could not build SRAMs...memory compiler error maybe?"
    echo exit 13
fi


