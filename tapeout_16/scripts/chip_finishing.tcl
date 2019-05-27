
### Tool Settings
setDesignMode -process 16

set_interactive_constraint_modes [all_constraint_modes -active]

## Chip Finishing
addFiller -fitGap -cell "DCAP8BWP64P90 DCAP32BWP32P90 DCAP16BWP32P90 DCAP8BWP16P90 DCAP4BWP16P90 FILL64BWP16P90 FILL32BWP16P90 FILL16BWP16P90 FILL8BWP16P90 FILL4BWP16P90 FILL3BWP16P90 FILL2BWP16P90 FILL1BWP16P90"
ecoRoute -target
#create_net -name RTE_ANA 
#create_net -name POC_ANA -ground -physical
#create_net -name ESD_ANA -ground -physical
#
#foreach x [get_property [get_cells -filter "full_name=~*pad_ana* || full_name=~*ANA*"] full_name] {                                                                                  
#  connect_pin -net RTE_ANA   -pin RTE -inst $x
#  connect_global_net ESD_ANA -netlist_override -pin ESD -inst $x
#  connect_global_net POC_ANA -pin POCCTRL -inst $x
#}
#
#create_net -name RTE_DIG 
#create_net -name ESD_DIG -ground -physical
#create_net -name POC_DIG -ground -physical
#foreach x [get_property [add_to_collection [get_cell -of [get_nets -of [get_ports {*S3* pad_t* pad_clk_in* pad_reset_in*}]]] [get_cells {IOPAD_S3_*VDD_* IOPAD_S3_*VDDPST_* *POC_DIG *RTE_DIG}]] full_name] {
#  connect_pin -net RTE_DIG  -pin RTE -inst $x
#  connect_global_net ESD_DIG  -netlist_override -pin ESD -inst $x
#  connect_global_net POC_DIG -pin POCCTRL -inst $x
#}
#
#create_net -name RTE_DIG2
#create_net -name ESD_DIG2 -ground -physical
#create_net -name POC_DIG2 -ground -physical
#foreach x [get_property [add_to_collection [get_cell -of [get_nets -of [get_ports {*S0*}]]] [get_cells {IOPAD_S0_*VDD_* IOPAD_S0_*VDDPST_* *POC_DIG2 *RTE_DIG2}]] full_name] {
#  connect_pin -net RTE_DIG2  -pin RTE -inst $x
#  connect_global_net ESD_DIG2 -netlist_overrid -pin ESD -inst $x
#  connect_global_net POC_DIG2 -pin POCCTRL -inst $x
#}
#
#foreach x [get_property [add_to_collection [get_cell -of [get_nets -of [get_ports {*S1*}]]] [get_cells {IOPAD_S1_*VDD_* IOPAD_S1_*VDDPST_*}]] full_name] {
#  connect_pin -net RTE_DIG2  -pin RTE -inst $x
#  connect_global_net ESD_DIG2 -netlist_overrid -pin ESD -inst $x
#  connect_global_net POC_DIG2 -pin POCCTRL -inst $x
#}
#
#foreach x [get_property [add_to_collection [get_cell -of [get_nets -of [get_ports {*S2*}]]] [get_cells {IOPAD_S2_*VDD_* IOPAD_S2_*VDDPST_*}]] full_name] {
#  connect_pin -net RTE_DIG2  -pin RTE -inst $x
#  connect_global_net ESD_DIG2 -netlist_override -pin ESD -inst $x
#  connect_global_net POC_DIG2 -pin POCCTRL -inst $x
#} 


addInst -cell N16_SR_B_1KX1K_DPO_DOD_FFC_5x5 -inst sealring -physical -loc {-50 -50}
