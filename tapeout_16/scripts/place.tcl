source ../../scripts/tool_settings.tcl
#Constraints
set_interactive_constraint_modes [all_constraint_modes]
set_dont_touch true [get_nets -of */PAD]

set ports_out(tlx_fwd_clock)       [list \
  pad_tlx_fwd_toggle_o \
  pad_tlx_fwd_tvalid_p_o \
  pad_tlx_fwd_tdata_lo_p_o[*] \
  pad_tlx_fwd_tdata_hi_p_o[*] \
  pad_tlx_fwd_tvalid_t_o \
  pad_tlx_fwd_tdata_t_o[*] \
]

set_multicycle_path -setup 1 -to [get_ports $ports_out(tlx_fwd_clock)]
set_multicycle_path -hold 0 -to [get_ports $ports_out(tlx_fwd_clock)]

set_load 0.1 [all_outputs]


set_timing_derate -clock -early 0.97 -delay_corner _default_delay_corner_ 
set_timing_derate -clock -late 1.03  -delay_corner _default_delay_corner_
set_timing_derate -data -late 1.05  -delay_corner _default_delay_corner_

set_case_analysis 1 [get_pins -hier *DS0]
set_case_analysis 1 [get_pins -hier *DS1]
set_case_analysis 1 [get_pins -hier *DS2]
set_multicycle_path -setup 100 -through [get_pins -hier GlobalController_32_32_inst0/*read_data_in*]
set_multicycle_path -hold 99 -through [get_pins -hier GlobalController_32_32_inst0/*read_data_in*]

set_interactive_constraint_mode {}

### Place Design
place_opt_design -place

saveDesign init_place.enc -def -tcon -verilog

place_opt_design -opt

setTieHiLoMode -maxDistance 20 -maxFanout 16
addTieHiLo -cell "TIEHBWP16P90 TIELBWP16P90"
