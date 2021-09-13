echo "${num_words}x${word_size}m${mux_size}s" >> config.txt
mc_name=tsn16ffcllhdspsbsram_20131200_130a
export MC_HOME=inputs/adk/mc/${mc_name}
export PATH="${PATH}:inputs/adk/mc/MC2_2013.12.00.f/bin"
sram_name="ts1n16ffcllsblvtc${num_words}x${word_size}m${mux_size}s"
if [ $partial_write == True ]; then
  sram_name+="w"
fi

sram_name+="_130a"

# Compile the memories and capture the output in a log.
# Note that the compiler itself apparently never exits with nonzero status,
# regardless of errors flagged during execution (??)

cmd="./inputs/adk/mc/${mc_name}/tsn16ffcllhdspsbsram_130a.pl -file config.txt -NonBIST -NonSLP -NonDSLP -NonSD"
if [ ! $partial_write == True ]; then
    cmd+=" -NonBWEB"
fi
eval $cmd |& tee mc.log

# Because compiler does not fail properly, we have to look in the log
# for success/failure. If compiler failed, try and find cached srams to use.
# In particular, we currently are getting this failure (sep 2021):
# 
#    FATAL (MC, 044): Failed to get license for feature
#    MC2-tsn16ffcllhdspsbsram-CLV or MC2-tsn16ffcllhdspsbsram-CPV 

if grep FATAL mc.log; then
    echo "**ERROR Looks like memory compiler flagged a fatal error"
    echo "Will try using cached SRAMs instead :("
    echo '+++ HACK TIME! Using cached srams because mem compiler failed.'
    set -x

    # Use latest gold build as the cache (if hack were less temporary,
    # would use parm / env var here).
    # The -P option says to use the physical directory structure
    # instead of following symbolic links

    gold=/sim/buildkite-agent/gold
    if ! test -e $gold; then
        echo "**ERROR Cannot find gold directory for cached srams"
        echo "I.e. '$gold' does not exist"
        echo "Also see $0"
        exit 13
    fi
    g=$(cd -P $gold; pwd)
    echo "Using gold cache '$g'"

    # Use first sram found in cache, so long as it has the right name (e.g. sram_name='ts1n16ffcllsblvtc2048x64m8sw_130a')

    sram_dir=$(find $g -name ${sram_name} | head -1)
    echo "Using srams found in dir '$sram_dir'"
    cp -rp ${sram_dir} .

    # Done with hack

    set +x; echo '--- continue...'
fi




# ##############################################################################
# USE_CACHED=True
# USE_CACHED=False
# if [ $USE_CACHED == True ]; then
# 
#     # Mar 2021 Temporary fix to get around expired memory-compiler license
#     echo '+++ HACK TIME! Using cached srams...'; set -x
# 
#     # Use latest gold build as the cache (if hack were less temporary,
#     # would use parm / env var here).
#     # The -P option says to use the physical directory structure
#     # instead of following symbolic links
#     gold=/sim/buildkite-agent/gold
#     if ! test -e $gold; then
#         echo "**ERROR Cannot find gold directory for cached srams"
#         echo "I.e. '$gold' does not exist"
#         echo "Also see $0"
#         exit 13
#     fi
#     g=$(cd -P $gold; pwd)
#     echo "Using gold cache '$g'"
# 
#     # Use first sram found in cache, so long as it has the right name (e.g. sram_name='ts1n16ffcllsblvtc2048x64m8sw_130a')
#     sram_dir=$(find $g -name ${sram_name} | head -1)
#     echo "Using srams found in dir '$sram_dir'"
#     cp -rp ${sram_dir} .
# 
#     # Done w/hack
#     set +x; echo '--- continue...'
# 
# else
#     cmd="./inputs/adk/mc/${mc_name}/tsn16ffcllhdspsbsram_130a.pl -file config.txt -NonBIST -NonSLP -NonDSLP -NonSD"
#     if [ ! $partial_write == True ]; then
#         cmd+=" -NonBWEB"
#     fi
#     eval $cmd |& tee mc.log
#     
# fi

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
    exit 13
fi

echo '--- continue...'

