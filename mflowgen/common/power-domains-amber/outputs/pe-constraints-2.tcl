set_voltage ${voltage_vdd} -object_list {VDD VDD_SW}
set_voltage ${voltage_gnd} -object_list {VSS}
save_upf upf_${dc_design_name}.upf
