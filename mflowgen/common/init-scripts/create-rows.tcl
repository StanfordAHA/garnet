#=========================================================================
# create-rows.tcl
#=========================================================================
# Author : 
# Date   : 

# delete existing rows
deleteRow -all

# create single/double height rows
createRow -site $ADK_CORE_SINGLE_HEIGHT
createRow -site $ADK_CORE_SINGLE_HEIGHT_ECO
createRow -site $ADK_CORE_DOUBLE_HEIGHT -noFlip
