#!/usr/bin/bash

# Can do e.g. "$0 215" to check dir /build/gold.215
# 
# Also used in per-checkin CI test e.g. pmg.yml:
#   commands:
#   - $TEST --need_space 30G full_chip tile_array Tile_PE --steps init --debug
#   - .buildkite/pipelines/check_pe_area.sh

function usage {
cat <<EOF

Usage:
  $0 < Tile_PE | Tile_MemCore > [ build_dir ] 

Examples:
  $0 Tile_PE          ; # Looks for tile starting in curdir
  $0 Tile_MemCore 377 ; # Looks for tile starting in /build/gold.377

EOF
}
if [ "$1" == "--help" ]; then usage; exit; fi

# Unpack the args

which_tile=$1
[ "$which_tile" == "pe"  ] && which_tile="Tile_PE"
[ "$which_tile" == "mem" ] && which_tile="Tile_MemCore"

if [ "$2" != "" ]; then
    cd /build/gold.$2/full_chip/*tile_array/*${which_tile}
fi

###################################################
# Assuming a ratio of 3:1 for mem:pe widths
# (current TSMC build = 93u and 279u respectively);
# assuming a max chip width of 4800u;
# assuming 24 pe columns and 8 mem columns;
# (equal to 48 pe columns);
# max pe size would be 4800/48 or ... 100u
# max mem sixe would be 300u

if   [ "$which_tile" == "Tile_PE" ];      then max_width=100
elif [ "$which_tile" == "Tile_MemCore" ]; then max_width=300
else
    echo "ERROR must specify either 'Tile_PE' or 'Tile_Memcore'"
    usage; exit 13
fi

cat <<EOF

--- FINAL CHECK: ${which_tile} total width must be < ${max_width}u
EOF

# Designed to run from $garnet directory

fp=*cadence-innovus-init/outputs/design.checkpoint/save.enc.dat/Tile_PE.fp.gz

# Uncomment to test failure mode
max_width=10

# Head Box: 0.0000 0.0000 93.1500 87.5520 [ i.e. 93w and 82.5h ]

echo "grep 'Head Box' $fp"
gunzip -c $fp | awk -v max_width=$max_width '
  /^Head Box/ {
    print "  " $0
    print "  Actual width = "$5
    if ($5 > max_width) {
      print ""
      printf( "**ERROR TILE width %d TOO BIG, should be < %d\n", $NF, max_width);
      print ""
      printf("+++ FAIL TILE width %d TOO BIG, should be < %d\n", $NF, max_width);
      print ""
      exit 13;
    }
    exit
  }
'


