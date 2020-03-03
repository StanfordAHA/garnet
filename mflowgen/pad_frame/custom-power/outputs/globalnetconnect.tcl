# Same as everyone else
connect_global_net VDD -type pgpin -pin VDD -inst *
connect_global_net VDD -type tiehi
connect_global_net VSS -type pgpin -pin VSS -inst *
connect_global_net VSS -type tielo
connect_global_net VDD -type pgpin -pin VPP -inst *
connect_global_net VSS -type pgpin -pin VBB -inst *

# I/O power nets
connect_global_net VDDPST -type pgpin -pin VDDPST -inst *
connect_global_net VSS    -type pgpin -pin VSSPST -inst * 
