# Same as everyone else
globalNetConnect VDD -type pgpin -pin VDD -inst *
globalNetConnect VDD -type tiehi
globalNetConnect VSS -type pgpin -pin VSS -inst *
globalNetConnect VSS -type tielo
globalNetConnect VDD -type pgpin -pin VPP -inst *
globalNetConnect VSS -type pgpin -pin VBB -inst *

# I/O power nets
globalNetConnect VDDPST -type pgpin -pin VDDPST -inst *
globalNetConnect VSS    -type pgpin -pin VSSPST -inst * 

# Dragonphy power nets
globalNetConnect VDD -type pgpin -pin DVDD -inst iphy -override
globalNetConnect VSS -type pgpin -pin DVSS -inst iphy -override
globalNetConnect AVDD -type pgpin -pin AVDD -inst iphy -override
globalNetConnect AVSS -type pgpin -pin AVSS -inst iphy -override
globalNetConnect CVDD -type pgpin -pin CVDD -inst iphy -override
globalNetConnect CVSS -type pgpin -pin CVSS -inst iphy -override
