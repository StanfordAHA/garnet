#!/usr/bin/bash

cat <<EOF

==============================================================================
FINAL CHECK: must have fewer than 4000 PE_PE cells

EOF

# Designed to run from $garnet directory

far=full_chip/*tile_array/*Tile_PE/*synthesis/results_syn/final_area.rpt

#  grep PE_PE $far | sed 's/  */ /g'
#  PE_inst0 Tile_PE_PE_unq1 4623 2072.926 941.491 3014.417 
#  WrappedPE_inst0$PE_inst0 Tile_PE_PE 4438 1936.380 909.332 2845.712 

grep PE_PE $far | awk '
{ printf("Found %4d cells of type \"%s\"\n", $3, $2) 
  if ($3 > 3000) { print "**ERROR - TOO MANY CELLS!"; exit 13; }
}
'
