# Same as everyone else
globalNetConnect VDD -type pgpin -pin VDD -inst *
globalNetConnect VDD -type tiehi
globalNetConnect VSS -type pgpin -pin VSS -inst *
globalNetConnect VSS -type tielo
globalNetConnect VSS -type pgpin -pin VPW -inst *
globalNetConnect VDD -type pgpin -pin VNW -inst *

# I/O pads
globalNetConnect VDDPST -type pgpin -pin VDDIO -inst *
globalNetConnect VSS    -type pgpin -pin VSSIO -inst * 
globalNetConnect VSS    -type pgpin -pin VSSC -inst * 
globalNetConnect VSS    -type pgpin -pin VSS_CM -inst * 
globalNetConnect VDD    -type pgpin -pin VDDC -inst * 

