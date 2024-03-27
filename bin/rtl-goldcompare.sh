#!/bin/bash

# ALSO SEE ../../aha/aha/bin/rtl-goldcheck.sh


# Looks like maybe goldcheck is used here:
# # PWD=/nobackup/steveri/github/garnet
# % grep -r goldcheck .buildkite/
# .buildkite/pipelines/aha-flow-pipeline.yml:  key: "goldcheck-amber"
# .buildkite/pipelines/aha-flow-pipeline.yml:  - set -x; /aha/aha/bin/rtl-goldcheck.sh amber
# .buildkite/pipelines/aha-flow-pipeline.yml:  - "goldcheck-amber"
# .buildkite/pipelines/pmg.yml:#   - 'bin/rtl-goldcheck.sh --use-docker $$IMAGE $$CONTAINER amber'
# .buildkite/pipelines/pmg.yml:  - 'bin/rtl-goldcheck.sh --use-docker $$IMAGE $$CONTAINER onyx'
# 
# So what's the plan?
# - unite the two goldchecks
# - add to $AHA version:
#     don't use this one, use the garnet version instead
#     redirecting to garnet version...(exec garnet/bin/whatevs)
# 
# 
# 
# 
# To fix lalr, need a clean branch
# A possible way forward:
# - leave goldcompare alone for now / undo changes in lalr branch
# - LATER: confine all the goldcompare stuff to garnet
# 
# 
# 
# To clean branch need to fix $GARNET/bin/rtl-goldcompare.sh
# All the gold compare stuff should be in garnet repo.
# Because garnet repo can exist apart from aha repo, but not vice versa.
# Where even does aha use goldcheck??? Nowheres!!
# 
#     # PWD=/nobackup/steveri/github/aha
#     % git branch
#     * regress-daemon
#     % grep -r goldcheck *
#     <nada>
# 
#     # PWD=/nobackup/steveri/github/aha
#     % git checkout master
#     % git pull
#     <nada>
# 
# So where does garnet repo use goldcheck?
# 
# # PWD=/nobackup/steveri/github/garnet
# % git branch
# * lalr
# % grep -r goldcheck *

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
    sed 's/clk_gate0 glb_clk_gate/clk_gate glb_clk_gate/' | # Treat gate0 same as gate :(
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
