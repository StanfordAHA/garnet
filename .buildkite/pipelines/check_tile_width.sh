#!/usr/bin/bash

# Searches for e.g. 'Tile_PE.fp.gz' and checks to see if tile width is
# within acceptable bounds.
# 
# Also used in per-checkin CI test e.g. pmg.yml:
#   commands:
#   - $TEST --need_space 30G full_chip tile_array Tile_PE --steps init --debug
#   - .buildkite/pipelines/check_pe_area.sh Tile_PE .

function usage {
cat <<EOF

Usage:
  $0 < Tile_PE | Tile_MemCore > <max_width> [ build_dir ] 

Examples:
  $0 Tile_PE 100                      ; # Look for tile starting in curdir
  $0 Tile_MemCore 300 /build/gold.377 ; # Look for tile starting in /build/gold.377

EOF
}
if [ "$1" == "--help" ]; then usage; exit; fi

# Unpack the args
which_tile=$1; max_width=$2; dir=$3

# Can use 'pe' or 'mem' shorthand
[ "$which_tile" == "pe"  ] && which_tile="Tile_PE"
[ "$which_tile" == "mem" ] && which_tile="Tile_MemCore"

# Search-dir defaults to curdir [and all its subdirs]
[ "$dir" == "" ] && dir="*"

cat <<EOF

--- FINAL CHECK: ${which_tile} total width must be < ${max_width}u
EOF

# Find floorplan doc and divide in two lines for printing e.g.
# line1="/build/gold.377/full_chip/19-tile_array/17-Tile_PE/"
# line2="17-cadence-innovus-init/checkpoints/.../Tile_PE.fp.gz"
fp=`find $dir -name ${which_tile}.fp.gz | head -1`
if ! [ "$fp" ]; then 
    echo "ERROR cannot find design file '${which_tile}.fp.gz' underneath dir '$dir'"
    usage; exit 13
fi
line1=`echo $fp | sed 's|^\(.*/\)[0-9]*[-][^0-9]*$|\1|'`
line2=`echo $fp | sed 's|^.*/\([0-9]*[-][^0-9]*$\)|\1|'`
line2=`echo $line2 | sed 's|\w*/design.checkpoint/save.enc.dat|...|'`
echo ""
printf "  Found design\n    %s\n      %s\n" $line1 $line2
echo ""

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


##############################################################################
# OLD
# 
# # Assuming a ratio of 3:1 for mem:pe widths
# # (current TSMC build = 93u and 279u respectively);
# # assuming a max chip width of 4800u;
# # assuming 24 pe columns and 8 mem columns;
# # (equal to 48 pe columns);
# # max pe size would be 4800/48 or ... 100u
# # max mem sixe would be 300u
# 
# if   [ "$which_tile" == "Tile_PE" ];      then max_width=100
# elif [ "$which_tile" == "Tile_MemCore" ]; then max_width=300
# else
#     echo "ERROR must specify either 'Tile_PE' or 'Tile_Memcore'"
#     usage; exit 13
# fi
