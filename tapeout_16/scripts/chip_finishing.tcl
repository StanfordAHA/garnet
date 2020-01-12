### Tool Settings
eval_legacy {setDesignMode -process 16}

eval_legacy {setMultiCpuUsage -localCpu 8}

set_interactive_constraint_modes [all_constraint_modes -active]

#netlist fixing for pad ring
create_net -name ESD_0 -ground -physical
create_net -name ESD_1 -ground -physical
create_net -name ESD_2 -ground -physical
create_net -name ESD_3 -ground -physical

create_net -name POC_0 -ground -physical
create_net -name POC_1 -ground -physical

create_net -name AVDD -power -physical
create_net -name AVSS -ground -physical
create_net -name CVDD -power -physical
create_net -name CVSS -ground -physical

create_net -name RTE_3
create_net -name RTE_DIG

foreach x [get_property [get_cells {*IOPAD*ext_clk_async* *IOPAD_bottom* *IOPAD_left* *IOPAD_right*}] full_name] { 
  connect_global_net ESD_0 -netlist_override -pin ESD -inst $x
  connect_global_net POC_0 -pin POCCTRL -inst $x
  connect_pin -net RTE_DIG -pin RTE -inst $x
}

foreach x [get_property [get_cells {*IOPAD*ext_clkn *IOPAD*ext_clkp *IOPAD*CVDD* *IOPAD*CVSS*}] full_name] {
  connect_global_net ESD_1 -netlist_override -pin ESD -inst $x
  connect_global_net CVDD -netlist_override -pin TACVDD -inst $x
  connect_global_net CVSS -netlist_override -pin TACVSS -inst $x
}

foreach x [get_property [get_cells {*IOPAD*CVDD* *IOPAD*CVSS*}] full_name] {
  connect_global_net CVDD -netlist_override -pin AVDD -inst $x
  connect_global_net CVSS -netlist_override -pin AVSS -inst $x
}

foreach x [get_property [get_cells {*IOPAD*AVDD* *IOPAD*AVSS* *IOPAD*ext_Vcm* *IOPAD*ext_Vcal*}] full_name] {
  connect_global_net ESD_2  -netlist_override -pin ESD -inst $x
  connect_global_net AVDD -netlist_override -pin TACVDD -inst $x
  connect_global_net AVSS -netlist_override -pin TACVSS -inst $x
}

foreach x [get_property [get_cells {*IOPAD*AVDD* *IOPAD*AVSS*}] full_name] {
  connect_global_net AVDD -netlist_override -pin AVDD -inst $x
  connect_global_net AVSS -netlist_override -pin AVSS -inst $x
}

foreach x [get_property [get_cells *IOPAD*clk_test*] full_name] {
  connect_global_net ESD_3  -netlist_override -pin ESD -inst $x
}

foreach x [get_property [get_cells {*IOPAD*jtag_intf* *IOPAD*ext_rstb* *IOPAD_ext_dump* *IOPAD*dom3*}] full_name] {
  connect_global_net ESD_3  -netlist_override -pin ESD -inst $x
  connect_global_net POC_1 -pin POCCTRL -inst $x
  connect_pin -net RTE_3 -pin RTE -inst $x
}


# Moved to top_garnet*.tcl
# eval_legacy {addInst -cell N16_SR_B_1KX1K_DPO_DOD_FFC_5x5 -inst sealring -physical -loc {-52.344 -53.7}}
