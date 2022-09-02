#!/bin/bash

# Find feature number for PowerDomainConfigReg, according to verilog.
# Compare to feature number specified in params file.
# ERROR if no matchy.

# Assumes verilog is the only file "inputs/*.v" and
# that params are in "inputs/pe-pd-params.tcl" etc.


function find_verilog_number {

    # Find feature number for PowerDomainConfigReg, according to verilog.

    # Needs to be able to detect at least three different patterns,
    # one each for steps synthesis, init (floorplan), and pwr-aware-gls.

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

    # inputs/design.vcs.pg.v in step pwr-aware-gls:
    #  105643 module Tile_PE (
    #  127226    Tile_PE_PowerDomainConfigReg PowerDomainConfigReg_inst0 (
    #  127269         .config_write({ FEATURE_AND_13_out }),
    #  127306         .VSS(VSS));

    # Example:
    #    % $0 inputs/design*.v
    #    13


    BEGIN="PowerDomainConfigReg PowerDomainConfigReg_inst0"
    # END="config_write"
    END=";"
    cat $1 | sed -n '/^module Tile_PE *(/,/endmodule/p' \
        | sed -n "/$BEGIN/,/$END/p" \
        | grep FEATURE_AND \
        | sed 's/.*FEATURE_AND_//' | sed 's/_out.*//'
}

function find_param_number {
    # Expecting to see something like
    # "set pe_power_domain_config_reg_addr 13"
    cat $1 | awk '/^set pe_power_domain_config_reg_addr/{print $3; exit}'
}

vn=`find_verilog_number $1`
echo "Verilog says PowerDomainConfigReg has feature number $vn"

pn=`find_param_number inputs/pe-pd-params.tcl`
echo "Parameters say feature number should be $pn"

if [ "$pn" == "$vn" ]; then
    echo "Hey looks like we are good."
else
    echo "**ERROR PowerDomainConfig feature numbers don't match, design will surely fail"
    exit 13
fi

