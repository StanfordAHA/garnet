

#------------------------------------------------------------------------
# Dont use cells list 
#------------------------------------------------------------------------


# Some cells see following warnings during placement:
#**WARN: (IMPOPT-3564):  The following cells are set dont_use temporarily by the tool 
# because there are no rows defined for their technology site, 
# or they are not placeable in any power domain, 
# or their pins cannot be snapped to the tracks. 
# To avoid this message, review the floorplan, msv setting, 
# the library setting or set manually those cells as dont_use.
#**WARN: (IMPSP-270):    Cannot find a legal location for MASTER CELL 'XNR4D0BWP16P90'.
#**WARN: (IMPSP-270):    Cannot find a legal location for MASTER CELL 'XOR4D0BWP16P90'.
# Set don't use on these cells upfront in P&R as well as in synthesis

set_dont_use [get_lib_cells {*/*XNR4D0BWP16P90* */*MUX2D1BWP16P90* */*XOR4D0BWP16P90* */*MUX2D0P75BWP16P90* */*CKLNQOPTBBD1BWP16P90* */*CKMUX2D4BWP16P90* */*CKMUX2D1BWP16P90* }]


