#netlist fixing for pad ring
addNet ESD_0 -ground -physical
addNet ESD_1 -ground -physical
addNet ESD_2 -ground -physical
addNet ESD_3 -ground -physical

addNet POC_0 -ground -physical
addNet POC_1 -ground -physical

addModulePort - AVSS bidi
addModulePort - AVDD bidi
addModulePort - CVSS bidi
addModulePort - CVDD bidi
addModulePort - ext_Vcal bidi

addNet AVDD -power -physical
addNet AVSS -ground -physical
addNet CVDD -power -physical
addNet CVSS -ground -physical

# Dragonphy power pin
addNet ext_Vcal -power -physical

addNet RTE_3
addNet RTE_DIG

globalNetConnect CVSS -netlistOverride -pin VSSPST1 -singleInstance IOPAD_top_cut_1
globalNetConnect VSS -netlistOverride -pin VSSPST2 -singleInstance IOPAD_top_cut_1
globalNetConnect AVSS -netlistOverride -pin VSSPST1 -singleInstance IOPAD_top_cut_2
globalNetConnect CVSS -netlistOverride -pin VSSPST2 -singleInstance IOPAD_top_cut_2
globalNetConnect VSS -netlistOverride -pin VSSPST1 -singleInstance IOPAD_top_cut_3
globalNetConnect AVSS -netlistOverride -pin VSSPST2 -singleInstance IOPAD_top_cut_3

#dragonphy power nets
globalNetConnect AVDD -type pgpin -pin AVDD -inst iphy -override
globalNetConnect AVSS -type pgpin -pin AVSS -inst iphy -override
globalNetConnect CVDD -type pgpin -pin CVDD -inst iphy -override
globalNetConnect CVSS -type pgpin -pin CVSS -inst iphy -override
globalNetConnect ext_Vcal -type pgpin -pin ext_Vcal -inst iphy -override
attachTerm -noNewPort ANAIOPAD_ext_Vcal AIO ext_Vcal


# Add port for each iphy-to-bump connection
set bump_to_iphy [list \
  ext_rx_inp \
  ext_rx_inn \
  ext_rx_inp_test \
  ext_rx_inn_test \
  ext_clkp \
  ext_clkn \
]

set iphy_to_bump [list \
  clk_out_p \
  clk_out_n \
  clk_trig_p \
  clk_trig_n \
  ext_tx_outp \
  ext_tx_outn \
]

set pad_to_iphy [list \
  ext_Vcm \
  ext_mdll_clk_refp \
  ext_mdll_clk_refn \
  ext_mdll_clk_monp \
  ext_mdll_clk_monn \
  ext_clk_async_p \
  ext_clk_async_n \
]

foreach port $bump_to_iphy {
  deleteNet $port
  addModulePort - $port input
  attachTerm -noNewPort iphy $port $port
}

foreach port $iphy_to_bump {
  if {[sizeof_collection [get_nets -quiet $port]] > 0} {
    deleteNet $port
  }
  addModulePort - $port output
  attachTerm -noNewPort iphy $port $port
}

foreach port $pad_to_iphy {
  deleteNet $port
  addModulePort - $port input
  attachTerm -noNewPort iphy $port $port
  attachTerm -noNewPort ANAIOPAD_$port AIO $port
}

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

foreach x [get_property [get_cells *IOPAD*ext_mdll*] full_name] {
  globalNetConnect ESD_3  -netlistOverride -pin ESD -singleInstance $x
}

foreach x [get_property [get_cells {*IOPAD*jtag_intf* *IOPAD*ext_rstb* *IOPAD_ext_dump* *IOPAD*dom3* *IOPAD*freq_lvl_cross* *IOPAD*ramp_clock*}] full_name] {
  globalNetConnect ESD_3  -netlistOverride -pin ESD -singleInstance $x
  globalNetConnect POC_1 -pin POCCTRL -singleInstance $x
  #connect_pin -net RTE_3 -pin RTE -singleInstance $x
  attachTerm -noNewPort $x RTE RTE_3
}

