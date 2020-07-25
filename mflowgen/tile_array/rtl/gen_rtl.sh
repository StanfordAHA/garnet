#!/bin/bash

# Will this work? We're going to try and destroy and completely
# replace the directory we're currently in, which presumably is
# something like 'full_chip/14-tile_array/9-rtl'

echo TILE_ARRAY GEN_RTL BEGINS HERE
set -x

# Should be in some dir hierarchy e.g. 'full_chip/14-tile_array/9-rtl'
pwd

# Want to be in e.g. 'full_chip/14-tile_array'
cd ..; pwd

echo '-------'
make status
echo '-------'
make -n synopsys-dc-synthesis | grep 'mkdir.*output' | sed 's/.output.*//' | sed 's/mkdir -p/  make/'
echo '-------'


# Hope MFLOWGEN_PATH is set correctly (and/or does it matter?
echo MFLOWGEN_PATH=$MFLOWGEN_PATH

# Okay here goes nothin
mflowgen stash link --path /home/ajcars/tile-array-rtl-stash/2020-0724-mflowgen-stash-75007d
mflowgen stash pull --hash 2fbc7a

# Did it work???
echo '-------'
make status
echo '-------'
make -n synopsys-dc-synthesis | grep 'mkdir.*output' | sed 's/.output.*//' | sed 's/mkdir -p/  make/'
echo '-------'



set +x
echo TILE_ARRAY GEN_RTL ENDS HERE
