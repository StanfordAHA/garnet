### Tool Settings
eval_legacy {setDesignMode -process 16}

eval_legacy {source $::env(TAPEOUT)/scripts/tool_settings.tcl}
eval_legacy {setMultiCpuUsage -localCpu 8}

set_interactive_constraint_modes [all_constraint_modes -active]

## Chip Finishing
# Add fillers by quadrant
eval_legacy {
  set die_size 4899.96
  set die_size_half [expr $die_size / 2]
  set num_strips 10
  set strip_width [expr $die_size / $num_strips]
  set cell_list \
"FILL64BWP16P90 FILL64BWP16P90LVT FILL64BWP16P90ULVT FILL32BWP16P90 FILL32BWP16P90LVT FILL32BWP16P90ULVT FILL16BWP16P90 FILL16BWP16P90LVT FILL16BWP16P90ULVT FILL8BWP16P90 FILL8BWP16P90LVT FILL8BWP16P90ULVT FILL4BWP16P90 FILL4BWP16P90LVT FILL4BWP16P90ULVT FILL3BWP16P90 FILL3BWP16P90LVT FILL3BWP16P90ULVT FILL2BWP16P90 FILL2BWP16P90LVT FILL2BWP16P90ULVT FILL1BWP16P90 FILL1BWP16P90LVT FILL1BWP16P90ULVT DCAP64BWP16P90 DCAP64BWP16P90LVT DCAP64BWP16P90ULVT DCAP32BWP16P90 DCAP32BWP16P90LVT DCAP32BWP16P90ULVT DCAP16BWP16P90 DCAP16BWP16P90LVT DCAP16BWP16P90ULVT DCAP8BWP16P90 DCAP8BWP16P90LVT DCAP8BWP16P90ULVT DCAP4BWP16P90 DCAP4BWP16P90LVT DCAP4BWP16P90ULVT"
  setFillerMode -scheme locationFirst \
             -minHole true \
             -fitGap true \
             -keepFixed true \
             -diffCellViol false \
             -core $cell_list \
             -add_fillers_with_drc false

  for {set i 0} {$i < $num_strips} {incr i} {
    set left [expr max(0, ($i * $strip_width) - 2)]
    set right [expr min($die_size, ($i + 1) * $strip_width)]
    echo "starting strip $i left: $left right $right"
    addFiller -markFixed -area [list $left 0 $right $die_size]
    echo "finished strip $i left: $left right $right"
    #if {[expr ($i % 2) == 1]} {
    #  write_db "fill_$i.db"
    #}
  }
}
#ecoRoute -target

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

foreach x [get_property [get_cells {*IOPAD*ext_clk_async* *IOPAD_bottom* *IOPAD_left* *IOPAD_right*}] full_name] {                                                                                  
  connect_global_net ESD_0 -netlist_override -pin ESD -inst $x
  connect_global_net POC_0 -pin POCCTRL -inst $x
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


eval_legacy {addInst -cell N16_SR_B_1KX1K_DPO_DOD_FFC_5x5 -inst sealring -physical -loc {-52.344 -53.7}}
