
#------------------------------------------------------------------------
# Connect backup power pins of power management cells 
# ------------------------------------------------------------------------


# Route secondary power pins for AON Buf/Invs
# Treats PG nets as signal routes so the backup
# power pins can be connected to the aon-supply

routePGPinUseSignalRoute -all

