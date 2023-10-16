#=========================================================================
# generate_db.tcl
#=========================================================================
# Generate db from a lib file (using Synopsys DC)
#
# For the library name, look at the top of the .lib file:
#
#     library (NangateOpenCellLibrary) (...)
#
# Author : Christopher Torng
# Date   : November 11, 2019
#

set sram_lib_name "$::env(sram_name)_$::env(corner)"
enable_write_lib_mode
read_lib ../../outputs/sram_tt.lib
write_lib -format db $sram_lib_name -output ../../outputs/sram_tt.db

exit

