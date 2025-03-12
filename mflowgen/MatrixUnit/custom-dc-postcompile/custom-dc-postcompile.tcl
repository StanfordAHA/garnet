#=========================================================================
# Post-compile DC commands file
#=========================================================================

# We are manually ungrouping all references to mantle_wire* modules after 
# compilation because doing so before compilation caused hi,lo -> tile_id
# connection on pe and memory tiles to be optimized away and replaced with 
# tie cells.
#set_dont_touch [get_references *mantle_wire*] false
#ungroup [get_references *mantle_wire*]
