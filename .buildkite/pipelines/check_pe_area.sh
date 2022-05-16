#!/usr/bin/bash

# Can do e.g. "check_pe_area.sh 215" to check dir /build/gold.215
# else defaults to curdir
if [ "$1" != "" ]; then cd /build/gold.$1; fi


cat <<EOF

--- FINAL CHECK: Tile_PE total area must be < 7500 u^2

EOF

# Designed to run from $garnet directory

pe_dir=full_chip/*tile_array/*Tile_PE
echo `pwd`/
echo $pe_dir

# "echo" to unglob why not
resdir=`echo $pe_dir/*synthesis/results_syn`
egrep ^Tile_PE $resdir/final_area.rpt | awk -v max_area=8500 '
{ printf("Total area: %d\n", $NF);
  if ($NF > max_area) {
    print ""
    print  "**ERROR '$resdir/final_area.rpt'"
    printf("**ERROR TILE area %d TOO BIG, should be < %d\n", $NF, max_area);
    printf("+++ FAIL TILE area %d TOO BIG, should be < %d\n", $NF, max_area);
    print ""; exit 13; }}
'



#######################################################################################
# Sample input:
# 
# Instance                Module          Cell Count  Cell Area  Net Area   Total Area 
# -------------------------------------------------------------------------------------
# Tile_PE                                      10188   4772.442  2214.860     6987.303 
#   PE_inst0              Tile_PE_PE_unq1       2955   1226.431   655.597     1882.028 
#     WrappedPE_inst0...  Tile_PE_PE            2770   1089.521   622.730     1712.252 



#######################################################################################
# Sample output:
# 
# +++ FINAL CHECK: Tile_PE total area must be < 7500 u^2
# 
# /sim/buildkite-agent/builds/bigjobs-1/tapeout-aha/mflowgen/
# full_chip/17-tile_array/17-Tile_PE
# Total area: 8573
# 
# **ERROR full_chip/17-tile_array/17-Tile_PE/13-cadence-genus-synthesis/results_syn/final_area.rpt
# **ERROR TILE area 8573 TOO BIG, should be < 7500



##############################################################################
# Previous runs and errors
# 
# 
# BEFORE peak update, size=7282: /build/gold.211/full_chip/\
# 17-tile_array/17-Tile_PE/14-cadence-genus-synthesis/results_syn
# =======================================================================
# Instance                        Module          Cell Count   Total Area 
# -----------------------------------------------------------------------
# Tile_PE                                              10834     7282.370 
#   PE_inst0                      Tile_PE_PE_unq1       3491     2130.352 
#     WrappedPE_inst0$PE_inst0    Tile_PE_PE            3304     1960.458 
# =======================================================================
# 
# 
# AFTER peak update, size=8619 (TOO BIG): /build/gold.214/full_chip/\
# 17-tile_array/17-Tile_PE/14-cadence-genus-synthesis/results_syn
# =======================================================================
# Instance                        Module          Cell Count   Total Area 
# -----------------------------------------------------------------------
# Tile_PE                                              12535     8619.954 
#   PE_inst0                      Tile_PE_PE_unq1       4623     3014.417 
#     WrappedPE_inst0$PE_inst0    Tile_PE_PE            4438     2845.712 
# =======================================================================
# 
# 
# Rerun 214/AFTER except @ 4ns instead of 1.1, size=6985
# =======================================================================
# Instance                        Module          Cell Count   Total Area 
# -----------------------------------------------------------------------
# Tile_PE                                              10137     6985.531 
#   PE_inst0                       Tile_PE_PE_unq1      2930     1887.316 
#     WrappedPE_inst0$PE_inst0     Tile_PE_PE           2746     1717.927 
# =======================================================================
