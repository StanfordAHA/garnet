
### Tool Settings
setDesignMode -process 16

source $::env(TAPEOUT)/scripts/tool_settings.tcl
setMultiCpuUsage -localCpu 8

set_interactive_constraint_modes [all_constraint_modes -active]

## Chip Finishing
addFiller -fitGap -cell "DCAP8BWP64P90 DCAP32BWP32P90 DCAP16BWP32P90 DCAP8BWP16P90 DCAP4BWP16P90 FILL64BWP16P90 FILL32BWP16P90 FILL16BWP16P90 FILL8BWP16P90 FILL4BWP16P90 FILL3BWP16P90 FILL2BWP16P90 FILL1BWP16P90"
#ecoRoute -target

#netlist fixing for pad ring
create_net -name ESD_0 -ground -physical
create_net -name ESD_1 -ground -physical
create_net -name ESD_2 -ground -physical
create_net -name ESD_3 -ground -physical

create_net -name POC_0 -ground -physical
create_net -name POC_1 -ground -physical

foreach x [get_property [get_cells {*IOPAD*ext_clk_async* *IOPAD_bottom* *IOPAD_left* *IOPAD_right*}] full_name] {                                                                                  
  connect_global_net ESD_0 -netlist_override -pin ESD -inst $x
  connect_global_net POC_0 -pin POCCTRL -inst $x
}

foreach x [get_property [get_cells {*IOPAD*ext_clk_async* *IOPAD*CVDD* *IOPAD*CVSS*}] full_name] {                                                                                  
  connect_global_net ESD_1 -netlist_override -pin ESD -inst $x
}

foreach x [get_property [get_cells {*IOPAD*AVDD* *IOPAD*AVSS* *IOPAD*ext_Vcm* *IOPAD*ext_Vcal*}] full_name] {
  connect_global_net ESD_2  -netlist_override -pin ESD -inst $x
}

foreach x [get_property [get_cells *IOPAD*clk_test*] full_name] {
  connect_global_net ESD_3  -netlist_override -pin ESD -inst $x
}

foreach x [get_property [get_cells {*IOPAD*jtag_intf* *IOPAD*ext_rstb* *IOPAD_ext_dump* *IOPAD*dom3*}] full_name] {
  connect_global_net ESD_3  -netlist_override -pin ESD -inst $x
  connect_global_net POC_1 -pin POCCTRL -inst $x
}


addInst -cell N16_SR_B_1KX1K_DPO_DOD_FFC_5x5 -inst sealring -physical -loc {-52.344 -53.7}
