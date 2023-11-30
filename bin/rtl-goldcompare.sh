#!/bin/bash

#########################################################################
# FYI THIS SCRIPT IS NO LONGER USED MAYBE. INSTEAD, WE USE THE VCOMPARE #
# FUNCTION DEFINED INTERNALLY IN $AHA_REPO/aha/bin/rtl-goldcheck.sh     #
#########################################################################

cmd=$0; HELP="
DESCRIPTION
  Compare two verilog files, ignoring non-functional diffs mostly ish.

EXAMPLES
  $cmd file1.v file2.v
  $cmd <(gunzip -c file1.v.gz) <(gunzip -c file2.v.gz)
"
[ "$1" == "--help" ] && echo "$HELP" && exit
[ "$1" == "" ] && echo "$HELP" && exit

f1=$1; f2=$2

#########################################################################
# FYI THIS SCRIPT IS NO LONGER USED MAYBE. INSTEAD, WE USE THE VCOMPARE #
# FUNCTION DEFINED INTERNALLY IN $AHA_REPO/aha/bin/rtl-goldcheck.sh     #
#########################################################################

# Need 'sed s/unq...' to handle the case where both designs are
# exactly the same but different "unq" suffixes e.g.
#     < Register_unq3 Register_inst0 (
#     > Register_unq2 Register_inst0 (
#
# Need 's/_O._value_O/...' because generator seems e.g. to randomly assign
# the equivalent values 'PE_onyx_inst_onyxpeintf_O3_value_O' and '...O4_value_O' :(

#########################################################################
# FYI THIS SCRIPT IS NO LONGER USED MAYBE. INSTEAD, WE USE THE VCOMPARE #
# FUNCTION DEFINED INTERNALLY IN $AHA_REPO/aha/bin/rtl-goldcheck.sh     #
#########################################################################

function vcompare {
    cat $1 |
    sed 's/_O._value_O/_Ox_value_O/g' | # Treat all zeroes as equivalent
    sed 's/,$//'         | # No trailing commas
    sed 's/_unq[0-9*]//' | # Canonicalize unq's
    sed '/^\s*$/d'       | # No blank lines
    sort                 | # Out-of-order is okay
    cat
}
printf "\n"
echo "Comparing `vcompare $f1 | wc -l` lines of $f1"
echo "versus    `vcompare $f2 | wc -l` lines of $f2"
printf "\n"

echo "diff $f1 $f2"
diff -Bb -I Date <(vcompare $f1) <(vcompare $f2)

#########################################################################
# FYI THIS SCRIPT IS NO LONGER USED MAYBE. INSTEAD, WE USE THE VCOMPARE #
# FUNCTION DEFINED INTERNALLY IN $AHA_REPO/aha/bin/rtl-goldcheck.sh     #
#########################################################################
