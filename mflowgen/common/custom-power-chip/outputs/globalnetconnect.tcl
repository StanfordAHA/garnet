set WHICH_SOC "onyx"
if { [info exists ::env(WHICH_SOC)] } { set WHICH_SOC $::env(WHICH_SOC) }

# Same as everyone else
globalNetConnect VDD -type pgpin -pin VDD -inst *
globalNetConnect VDD -type tiehi
globalNetConnect VSS -type pgpin -pin VSS -inst *
globalNetConnect VSS -type tielo
if { $WHICH_SOC == "amber" } {
globalNetConnect VDD -type pgpin -pin VPP -inst *
globalNetConnect VSS -type pgpin -pin VBB -inst *
} else {
globalNetConnect VSS -type pgpin -pin VPW -inst *
globalNetConnect VDD -type pgpin -pin VNW -inst *
}

if { $WHICH_SOC == "amber" } {
# I/O power nets
globalNetConnect VDDPST -type pgpin -pin VDDPST -inst *
globalNetConnect VSS    -type pgpin -pin VSSPST -inst * 
} else {
# I/O pads
globalNetConnect VDDPST -type pgpin -pin VDDIO -inst *
globalNetConnect VSS    -type pgpin -pin VSSIO -inst * 
globalNetConnect VSS    -type pgpin -pin VSSC -inst * 
globalNetConnect VSS    -type pgpin -pin VSS_CM -inst * 
globalNetConnect VDD    -type pgpin -pin VDDC -inst * 
}

if { $WHICH_SOC == "amber" } {
# Dragonphy power nets
globalNetConnect VDD -type pgpin -pin DVDD -inst iphy -override
globalNetConnect VSS -type pgpin -pin DVSS -inst iphy -override
globalNetConnect AVDD -type pgpin -pin AVDD -inst iphy -override
globalNetConnect AVSS -type pgpin -pin AVSS -inst iphy -override
globalNetConnect CVDD -type pgpin -pin CVDD -inst iphy -override
globalNetConnect CVSS -type pgpin -pin CVSS -inst iphy -override
}
