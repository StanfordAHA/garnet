#!/bin/bash

cmd=$0; HELP="
DESCRIPTION
  Compare two verilog files, ignoring non-functional diffs mostly ish.

EXAMPLES
  $cmd file1.v file2.v
  $cmd <(gunzip -c file1.v.gz) <(gunzip -c file2.v.gz)
"
[ "$1" == "--help" ] && echo "$HELP" && exit
[ "$1" == "" ] && echo "$HELP" && exit

# Need 'sed s/unq...' to handle the case where both designs are
# exactly the same but different "unq" suffixes e.g.
#     < Register_unq3 Register_inst0 (
#     > Register_unq2 Register_inst0 (
#
# Need 's/_O._value_O/...' because generator seems e.g. to randomly assign
# the equivalent values 'PE_onyx_inst_onyxpeintf_O3_value_O' and '...O4_value_O' :(


#     sed 's/clk_gate_unq/clk_gate/'    | # Treat clk_gate_unq same as clk_gate :(

set -o pipefail # FAIL if any command in any pipe fails from here down

function vcompare {
    cat $1 |
    sed 's/_O._value_O/_Ox_value_O/g'                     | # Treat all zeroes as equivalent
    sed 's/clk_gate0 glb_clk_gate/clk_gate glb_clk_gate' | # Treat gate0 same as gate :(
    sed 's/,$//'           | # No trailing commas
    sed 's/unq[0-9*]/unq/' | # Canonicalize unq's
    sed '/^\s*$/d'         | # No blank lines
    sort                   | # Out-of-order is okay
    cat
}

# FAIL if something is wrong with vcompare
errmsg='vcompare script failed in rtl-goldcompare.sh'
if ! vcompare $1 > /dev/null; then echo $errmsg; exit 13; fi
if ! vcompare $2 > /dev/null; then echo $errmsg; exit 13; fi

# vcompare $1 > /dev/null || echo 'vcompare script failed in rtl-goldcompare.sh'
# vcompare $2 > /dev/null || echo 'vcompare script failed in rtl-goldcompare.sh'

# Do the final compare
diff -Bb -I Date <(vcompare $1) <(vcompare $2)
