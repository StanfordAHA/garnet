
#-------------------------------------------------------------------------
# Endcap and well tap insertion 
#-------------------------------------------------------------------------
# TSMC16 requires specification of different taps/caps for different
# locations/orientations, which the foundation flow does not natively support

# Insert tap cells only on the boundary for SD domain
# Power switches will provide substrate connection for the core
# Insert both tap cells in the entire AON domain (since they dont have power switches)

if {[expr {$ADK_END_CAP_CELL == ""} && {$ADK_WELL_TAP_CELL == ""}]} {
    
    adk_add_endcap_well_taps_sd_pwr_domains
    adk_add_end_caps
    adk_add_endcap_well_taps_aon_pwr_domains  
}

