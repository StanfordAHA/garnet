#!/bin/bash

# Prep:
# docker cp ~/tmpdir/test_amber_rtl_build/ $container:/aha/garnet/tests

# Then, in docker:
#     cd /aha/garnet
#     tests/test_amber_rtl_build/amber-rtl-build-check.sh |& tee amber-build.log

# I am e.g. /aha/garnet/tests/test_amber_rtl_build/amber-rtl-build-check.sh
# Ref file is e.g. /aha/garnet/tests/test_amber_rtl_build/ref/garnet-4x2.v

# Do this inside docker:

set -x
# width=32  # slow 32x16
width=4   # quick 4x2

height=$((width/2))
flags="--width $width --height $((width/2)) --pipeline_config_interval 8 -v --glb_tile_mem_size 256"
echo $flags

# Prep/clean
cd /aha
rm -rf garnet/genesis_verif
rm -f  garnet/garnet.v

# Build new rtl
export WHICH_SOC='amber'
source /aha/bin/activate; # Set up the build environment
aha garnet $flags

# Assemble final design.v
cd /aha/garnet
cp garnet.v genesis_verif/garnet.v
cat genesis_verif/* > design.v
cat global_buffer/systemRDL/output/glb_pio.sv >> design.v
cat global_buffer/systemRDL/output/glb_jrdl_decode.sv >> design.v
cat global_buffer/systemRDL/output/glb_jrdl_logic.sv >> design.v
cat global_controller/systemRDL/output/*.sv >> design.v

# Compare to ref
scriptpath=$0
scriptpath=`readlink $scriptpath || echo $scriptpath`  # Full path of script dir
scriptdir=${scriptpath%/*}  # E.g. "build_tarfile.sh" or "foo/bar"

ref=$scriptdir/ref/garnet-4x2.v

echo "--- Compare result to reference build"
f1=design.v
f2=$ref
function vcompare { sort $1 | sed 's/,$//' ;}

echo "How many diffs?"
diff -I Date <(vcompare $f1) <(vcompare $f2) | wc -l

printf "\nTop 4o diffs:\n"
diff -I Date <(vcompare $f1) <(vcompare $f2) | head -40
