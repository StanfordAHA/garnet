#!/bin/bash

# At its whim, magma may decide to change the address of the power
# domain config register. This script looks at the verilog to find the
# latest/current address and inserts it into the GLS test bench

# Find feature number for PowerDomainConfigReg, according to verilog.
function find_verilog_number {

    # Want to find this pattern in the input verilog
    #
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

# Testbench must be updated to use the proper feature address.
# if that assumption has changed, we will need to fix it

vn=`find_verilog_number inputs/design.vcs.pg.v`

echo ""
echo "Updating testbench to match verilog feature address '$vn'"
echo ""

# Test bench wants address in bits [23:16] of a 32-bit vector
# E.g. if address = 18 then vector = '00120000'
addr=`echo $vn | awk '{printf("%04X0000", $0)}'`

set -x
mv tb_Tile_PE.v tb_Tile_PE.v.orig
sed "s/___PDCONFIG_ADDR___/$addr/g" tb_Tile_PE.v.orig > tb_Tile_PE.v
diff tb_Tile_PE.v.orig tb_Tile_PE.v
