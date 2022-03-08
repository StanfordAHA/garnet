

#-------------------------------------------------------------------------
# Global net connections for PG pins
#-------------------------------------------------------------------------

# Connect VNW / VPW if any cells have these pins
# Connect tie cells power supply based on the power domains
# Connect power switch aon-power pin to aon-power supply

globalNetConnect VDD_SW -type tiehi -powerdomain TOP
globalNetConnect VDD    -type tiehi -powerdomain AON
globalNetConnect VSS    -type tielo
globalNetConnect VDD    -type pgpin -pin VPP -inst *
globalNetConnect VSS    -type pgpin -pin VBB -inst *
globalNetConnect VDD    -type pgpin -pin TVDD -inst *HDR*

