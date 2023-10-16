#=========================================================================
# innovus-pnr-config.tcl
#=========================================================================
# This script is used to configure Innovus before running P&R. The
# configuration is dependent on the technology requirement and therefore
# should be confidential. 
# Author : 
# Date   : 

# This is a process defined in adk.tcl to hide sensitive information
adk_innovus_pnr_config

# Remove assigns without buffering (for regular signals)
remove_assigns

# Remove assigns by adding buffers (for top level ports)
remove_assigns -buffering
