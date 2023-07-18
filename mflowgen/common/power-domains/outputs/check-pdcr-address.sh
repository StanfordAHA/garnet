#!/bin/bash

# This script was developed for the amber build, has never been vetted for onyx.
if [ "$WHICH_SOC" == "amber" ]; then
    echo '--- check-pdcr-address.sh: Amber-only PowerDomainConfigReg correctness check'
else
    echo '--- check-pdcr-address.sh: Skip amber-only PowerDomainConfigReg correctness check'
    exit
fi

# In mflowgen steps "synthesis" or "init" (floorplan), check to see
# that PowerDomainConfigReg address in verilog matches param file.
# 
# ERROR if no matchy. Attempt to fix if ERROR.

########################################################################
# Function defs

# Find feature number for PowerDomainConfigReg, according to verilog.
function find_verilog_number {

    # Needs to be able to detect two different patterns,
    # one for the synthesis step, and one for init (floorplan).

    # inputs/design.v in step cadence-genus-synthesis:
    #   50947 module Tile_PE (
    #   51588 PowerDomainConfigReg PowerDomainConfigReg_inst0 (
    #   51593     .config_write(FEATURE_AND_13_out),
    #   51597 );

    # inputs/design.v in step cadence-innovus-init:
    #   29070 module Tile_PE(SB_T0_EAST_SB_IN_B1, SB_T0_EAST_SB_IN_B16,
    #   35710   Tile_PE_PowerDomainConfigReg PowerDomainConfigReg_inst0(.clk (clk),
    #   35729        (UNCONNECTED_HIER_Z843), .config_write (FEATURE_AND_13_out),
    #   35740        .reset (reset));

    BEGIN="PowerDomainConfigReg PowerDomainConfigReg_inst0"; END=";"

    cat $1 | sed -n '/^module Tile_PE *(/,/endmodule/p' \
        | sed -n "/$BEGIN/,/$END/p" \
        | grep FEATURE_AND \
        | sed 's/.*FEATURE_AND_//' | sed 's/_out.*//'
}

# Find feature number for PowerDomainConfigReg, according to param file.
function find_param_number {
    # Expecting to see something like
    # "set pe_power_domain_config_reg_addr 13"
    cat $1 | awk '/^set pe_power_domain_config_reg_addr/{print $3; exit}'
}

########################################################################
# Code begins here

# Parameter file should match verilog, else we complain and try to fix it.

vn=`find_verilog_number inputs/design.v`
pn=`find_param_number inputs/pe-pd-params.tcl`

echo ""
echo "Verilog says PowerDomainConfigReg has feature number $vn"
echo "Parameters say feature number should be $pn"
echo ""

function print_errmsg { echo """
    ERROR PowerDomainConfig feature numbers don't match.
    Design will surely fail if not fixed.

    To fix permanently, adjust var 'pe_power_domain_config_reg_addr' in
   'GARNET_HOME/mflowgen/common/power-domains/outputs/pe-pd-params.tcl', e.g.:

        set pe_power_domain_config_reg_addr $vn

    Meanwhile, hang on, I will attempt a temporary repair:
""";
}

if [ "$pn" == "$vn" ]; then
    echo "Hey looks like we are good."

else
    # ERROR message see above
    print_errmsg

    # Replace bad addr in params file w/ good addr from verilog.
    set -x
    mv inputs/pe-pd-params.tcl inputs/pe-pd-params.tcl.orig
    sed "s/^set pe_power_domain_config_reg_addr.*/set pe_power_domain_config_reg_addr $vn/" \
        inputs/pe-pd-params.tcl.orig > inputs/pe-pd-params.tcl

    # Don't want this to err out, just want to show the diffs
    diff inputs/pe-pd-params.tcl.orig inputs/pe-pd-params.tcl || echo okay
    set +x
fi

