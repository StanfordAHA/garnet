# Steveri 05-2020 copied from common/fc-netlist-fixing/outputs/netlist-fixing.tcl

# Steveri 05-2020 extra nets be wreaking havoc;
# eliminate anything not related to AVDD/AVSS, CVDD/CVSS.

#netlist fixing for pad ring

# addNet ESD_0 -ground -physical
# addNet ESD_1 -ground -physical
# addNet ESD_2 -ground -physical
# addNet ESD_3 -ground -physical
# 
# addNet POC_0 -ground -physical
# addNet POC_1 -ground -physical

addNet AVDD -power -physical
addNet AVSS -ground -physical
addNet CVDD -power -physical
addNet CVSS -ground -physical

# addNet RTE_3
# addNet RTE_DIG

# foreach x [get_property [get_cells {*IOPAD*ext_clk_async* *IOPAD_bottom* *IOPAD_left* *IOPAD_right*}] full_name] { 
#   globalNetConnect ESD_0 -netlistOverride -pin ESD -singleInstance $x
#   globalNetConnect POC_0 -pin POCCTRL -singleInstance $x
#   #connect_pin -net RTE_DIG -pin RTE -singleInstance $x
#   attachTerm -noNewPort $x RTE RTE_DIG
# }

foreach x [get_property [get_cells {*IOPAD*ext_clkn *IOPAD*ext_clkp *IOPAD*CVDD* *IOPAD*CVSS*}] full_name] {
#   globalNetConnect ESD_1 -netlistOverride -pin ESD -singleInstance $x
  globalNetConnect CVDD -netlistOverride -pin TACVDD -singleInstance $x
  globalNetConnect CVSS -netlistOverride -pin TACVSS -singleInstance $x
}

foreach x [get_property [get_cells {*IOPAD*CVDD* *IOPAD*CVSS*}] full_name] {
  globalNetConnect CVDD -netlistOverride -pin AVDD -singleInstance $x
  globalNetConnect CVSS -netlistOverride -pin AVSS -singleInstance $x
}

foreach x [get_property [get_cells {*IOPAD*AVDD* *IOPAD*AVSS* *IOPAD*ext_Vcm* *IOPAD*ext_Vcal*}] full_name] {
#   globalNetConnect ESD_2  -netlistOverride -pin ESD -singleInstance $x
  globalNetConnect AVDD -netlistOverride -pin TACVDD -singleInstance $x
  globalNetConnect AVSS -netlistOverride -pin TACVSS -singleInstance $x
}

foreach x [get_property [get_cells {*IOPAD*AVDD* *IOPAD*AVSS*}] full_name] {
  globalNetConnect AVDD -netlistOverride -pin AVDD -singleInstance $x
  globalNetConnect AVSS -netlistOverride -pin AVSS -singleInstance $x
}

# foreach x [get_property [get_cells *IOPAD*clk_test*] full_name] {
#   globalNetConnect ESD_3  -netlistOverride -pin ESD -singleInstance $x
# }
# 
# foreach x [get_property [get_cells {*IOPAD*jtag_intf* *IOPAD*ext_rstb* *IOPAD_ext_dump* *IOPAD*dom3*}] full_name] {
#   globalNetConnect ESD_3  -netlistOverride -pin ESD -singleInstance $x
#   globalNetConnect POC_1 -pin POCCTRL -singleInstance $x
#   #connect_pin -net RTE_3 -pin RTE -singleInstance $x
#   attachTerm -noNewPort $x RTE RTE_3
# }
