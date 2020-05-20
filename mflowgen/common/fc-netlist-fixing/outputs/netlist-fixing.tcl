#netlist fixing for pad ring
addNet ESD_0 -ground -physical
addNet ESD_1 -ground -physical
addNet ESD_2 -ground -physical
addNet ESD_3 -ground -physical

addNet POC_0 -ground -physical
addNet POC_1 -ground -physical

addNet AVDD -power -physical
addNet AVSS -ground -physical
addNet CVDD -power -physical
addNet CVSS -ground -physical

addNet RTE_3
addNet RTE_DIG

globalNetConnect CVSS -netlistOverride -pin VSSPST1 -singleInstance IOPAD_top_cut_1
globalNetConnect VSS -netlistOverride -pin VSSPST2 -singleInstance IOPAD_top_cut_1
globalNetConnect AVSS -netlistOverride -pin VSSPST1 -singleInstance IOPAD_top_cut_2
globalNetConnect CVSS -netlistOverride -pin VSSPST2 -singleInstance IOPAD_top_cut_2
globalNetConnect VSS -netlistOverride -pin VSSPST1 -singleInstance IOPAD_top_cut_3
globalNetConnect AVSS -netlistOverride -pin VSSPST2 -singleInstance IOPAD_top_cut_3

foreach x [get_property [get_cells {*IOPAD*ext_clk_async* *IOPAD_bottom* *IOPAD_left* *IOPAD_right*}] full_name] { 
  globalNetConnect ESD_0 -netlistOverride -pin ESD -singleInstance $x
  globalNetConnect POC_0 -pin POCCTRL -singleInstance $x
  #connect_pin -net RTE_DIG -pin RTE -singleInstance $x
  attachTerm -noNewPort $x RTE RTE_DIG
}

foreach x [get_property [get_cells {*IOPAD*ext_clkn *IOPAD*ext_clkp *IOPAD*CVDD* *IOPAD*CVSS*}] full_name] {
  globalNetConnect ESD_1 -netlistOverride -pin ESD -singleInstance $x
  globalNetConnect CVDD -netlistOverride -pin TACVDD -singleInstance $x
  globalNetConnect CVSS -netlistOverride -pin TACVSS -singleInstance $x
}

foreach x [get_property [get_cells {*IOPAD*CVDD* *IOPAD*CVSS* *IOPAD*AVDD* *IOPAD*AVSS*}] full_name] {
  globalNetConnect -disconnect -pin AVDD -singleInstance $x
  globalNetConnect -disconnect -pin AVSS -singleInstance $x
}

foreach x [get_property [get_cells {*IOPAD*AVDD* *IOPAD*AVSS* *IOPAD*ext_Vcm* *IOPAD*ext_Vcal*}] full_name] {
  globalNetConnect ESD_2  -netlistOverride -pin ESD -singleInstance $x
  globalNetConnect AVDD -netlistOverride -pin TACVDD -singleInstance $x
  globalNetConnect AVSS -netlistOverride -pin TACVSS -singleInstance $x
}

foreach x [get_property [get_cells *IOPAD*clk_test*] full_name] {
  globalNetConnect ESD_3  -netlistOverride -pin ESD -singleInstance $x
}

foreach x [get_property [get_cells {*IOPAD*jtag_intf* *IOPAD*ext_rstb* *IOPAD_ext_dump* *IOPAD*dom3*}] full_name] {
  globalNetConnect ESD_3  -netlistOverride -pin ESD -singleInstance $x
  globalNetConnect POC_1 -pin POCCTRL -singleInstance $x
  #connect_pin -net RTE_3 -pin RTE -singleInstance $x
  attachTerm -noNewPort $x RTE RTE_3
}

