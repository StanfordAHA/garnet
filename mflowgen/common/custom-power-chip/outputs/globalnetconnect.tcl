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
