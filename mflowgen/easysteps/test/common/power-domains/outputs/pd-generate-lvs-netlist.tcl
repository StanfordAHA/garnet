#=========================================================================
# generate-lvs-netlist.tcl
#=========================================================================

# Write netlist for LVS
#
# Exclude physical cells that have no devices in them (or else LVS will
# have issues). Specifically for filler cells, the extracted layout will
# not have any trace of the fillers because there are no devices in them.
# Meanwhile, the schematic generated from the netlist will show filler
# cells instances with VDD/VSS ports, and this will cause LVS to flag a
# "mismatch" with the layout.

# Exclude VDD_SW from top PG port

foreach x $ADK_LVS_EXCLUDE_CELL_LIST {
  append lvs_exclude_list [dbGet -u -e top.insts.cell.name $x] " "
}


saveNetlist -excludeLeafCell                   \
            -phys                              \
            -excludeCellInst $lvs_exclude_list \
            -excludeTopCellPGPort {VDD_SW}   \
            $vars(results_dir)/$vars(design).lvs.v



