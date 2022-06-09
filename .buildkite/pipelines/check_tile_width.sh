#!/usr/bin/bash

# Searches for e.g. 'Tile_PE.fp.gz' and checks to see if tile width is
# within acceptable bounds.
# 
# Also used in per-checkin CI test e.g. pmg.yml:
#   commands:
#   - $TEST --need_space 30G full_chip tile_array Tile_PE --steps init --debug
#   - .buildkite/pipelines/check_pe_area.sh Tile_PE --max 110

function usage {
cat <<EOF

Usage:
  $0 < Tile_PE | Tile_MemCore > --max <max_width> [ build_dir ] 

Examples:
  $0 Tile_PE --max 100                      ; # Look for tile starting in curdir
  $0 Tile_MemCore --max 300 /build/gold.377 ; # Look for tile starting in /build/gold.377

EOF
}
if [ "$1" == "--help" ]; then usage; exit; fi

# Unpack the args
which_tile=$1; dashdashmax=$2; max_width=$3; dir=$4

# Can use 'pe' or 'mem' shorthand
[ "$which_tile" == "pe"  ] && which_tile="Tile_PE"
[ "$which_tile" == "mem" ] && which_tile="Tile_MemCore"

if ! [ "$dashdashmax" == "--max" ]; then
    echo 'ERROR forgot "--max" arg'
    usage; exit 13
fi

# Search-dir defaults to curdir [and all its subdirs]
[ "$dir" == "" ] && dir="*"

cat <<EOF

+++ FINAL CHECK: ${which_tile} total width must be < ${max_width}u
EOF

# Find floorplan doc
fp=`find $dir -name ${which_tile}.fp.gz | head -1`
if ! [ "$fp" ]; then 
    echo "ERROR cannot find floorplan '${which_tile}.fp.gz' underneath dir '$dir'"
    usage; exit 13
fi
printf "  Looking at width in floorplan '%s'\n" ${which_tile}.fp.gz

# Look in $fp for tile box (llx lly urx ury)
# Head Box: 0.0000 0.0000 93.1500 87.5520 [ i.e. 93w and 82.5h ]
gunzip -c $fp | awk -v max_width=${max_width} '
  /^Head Box/ {
    width=$5
#     print "  " $0 " :: width=" width
    printf("  `%s` :: width=%s\n", $0, width)
    if (width > max_width) {
      print ""
      printf( "**ERROR TILE width %du TOO BIG, should be < %du\n", width, max_width);
      print ""
      printf("+++ FAIL TILE width %du TOO BIG, should be < %du\n", width, max_width);
      print ""
      exit 13;
    }
    exit
  }
'
echo ""
