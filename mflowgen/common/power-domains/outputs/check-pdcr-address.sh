#!/bin/bash

# What this script does:
# 
# - if we are in GLS step,
#   update testbench w/ correct address for PowerDomainConfigReg
# 
# - if we are in any other step (i.e. synthesis or init) check to
#   see that PDCR address in verilog matches parameters in parm file.
#   ERROR if no matchy. Attempt to fix if ERROR.

########################################################################
# Function defs

# Find feature number for PowerDomainConfigReg, according to verilog.
function find_verilog_number {

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
# GLS fix-up
function we_are_in_gls_step  { expr `pwd` : '.*gls' > /dev/null; }
if we_are_in_gls_step; then

    # Testbench must be updated to use the proper feature address.
    # if that assumption has changed, we will need to fix it

    vn=`find_verilog_number inputs/design.vcs.pg.v`

    echo ""
    echo "Updating testbench to match verilog feature address '$vn'"
    old_vector='___PDCONFIG_ADDR___'
    new_vector=`echo $vn | awk '{printf("%04X0000", $0)}'`
    echo "Replacing old test vector '$old_vector' w/ new vector '$new_vector'"
    echo ""

    set -x
    mv tb_Tile_PE.v tb_Tile_PE.v.orig
    sed "s/$old_vector/$new_vector/g" tb_Tile_PE.v.orig > tb_Tile_PE.v
    diff tb_Tile_PE.v.orig tb_Tile_PE.v
    set +x
    exit
fi

#########################################################################
# If we get this far, we are either in synthesis step or init step
# Parameter file should match verilog, else: that really should be fixed!

vn=`find_verilog_number inputs/design.v`
pn=`find_param_number inputs/pe-pd-params.tcl`

echo ""
echo "Verilog says PowerDomainConfigReg has feature number $vn"
echo "Parameters say feature number should be $pn"

function print_errmsg { echo """
ERROR PowerDomainConfig feature numbers don't match.
Design will surely fail if not fixed.
Hang on I will try and fix it for you.

To fix permanently, adjust var 'pe_power_domain_config_reg_addr' in
'GARNET_HOME/mflowgen/common/power-domains/outputs/pe-pd-params.tcl'
""";
}

if [ "$pn" == "$vn" ]; then
    echo "Hey looks like we are good."
else
    # Replace bad addr in params file w/ good addr from verilog.
    print_errmsg
    set -x
    mv inputs/pe-pd-params.tcl inputs/pe-pd-params.tcl.orig
    sed "s/^set pe_power_domain_config_reg_addr.*/set pe_power_domain_config_reg_addr $vn/" \
        inputs/pe-pd-params.tcl.orig > inputs/pe-pd-params.tcl
    diff inputs/pe-pd-params.tcl.orig inputs/pe-pd-params.tcl
    set +x
fi

