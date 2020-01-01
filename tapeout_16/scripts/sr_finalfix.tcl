# If all went well up to this point, there should be only 37 DRC
# errors left. This script is supposed to eliminate nine of them.
# The remaining 28 errors all stem from the bottom IOPAD placement
# problem, for which I haven't decided on a good solution yet...

########################################################################
# Tell nanorouter to operate only on selected nets
# Max 10 iterations, although I'm pretty sure one is enough (it's fast).
set_multi_cpu_usage -local_cpu 8
set_db route_design_selected_net_only true
set_db route_design_detail_end_iteration 10

########################################################################
# 1568581 M2 (first of three nanoroute violations)
puts "@file_info Fixing net 1568581, should take about 30 minutes"

# 1. Delete problem net
set n net:core_cgra_subsystem/GlobalBuffer_inst0/FE_OFN1613594_n_1568581
deselect_obj -all; select_obj $n
# check_drc -check_only selected_net
delete_routes -net $n

# 2. Delete nearby nets that block M3 attachment:
set n1 net:GarnetSOC_pad_frame/core_cgra_subsystem/GlobalBuffer_inst0/FE_OFN1614041_global_buffer_inst0_global_buffer_int_memory_bank_27_glbuf_memory_core_sram_to_mem_data_32
set n2 {net:GarnetSOC_pad_frame/core_cgra_subsystem/GlobalBuffer_inst0/global_buffer_inst0_global_buffer_int_memory_bank_27_glbuf_memory_core_memory_sram_gen_genblk1\[5\].Q_temp[38]}
delete_routes -net [list $n $n1 $n2]

# Redo problem net: expect this to take 15 min
deselect_obj -all; select_obj $n
route_design -no_placement_check
# Expect this to take about 15m

# Reattach (deleted) blocking nets: expect this to take 15 min
deselect_obj -all; select_obj [list $n1 $n2]
route_design -no_placement_check

########################################################################
# 391528 M2 (remaining two nanoroute violations)
puts "@file_info Fixing net 391528, should take about 30 minutes"

# One problem net and two blocking nets
set n net:GarnetSOC_pad_frame/core_u_proc_tlx/n_391528
set n1 net:GarnetSOC_pad_frame/core_u_proc_tlx/CTS_660
set n2 {net:GarnetSOC_pad_frame/core_u_proc_tlx/proc_subsys_dma0_upl330_engine_upl330_icache_upl330_icache_array_w2_icache_array\[11\][11]}

# Delete them all
select_obj [list $n $n1 $n2]
delete_routes -net [list $n $n1 $n2]

# Redo problem net: expect this to take 15 min
deselect_obj -all; select_obj $n
route_design -no_placement_check

# Reattach (deleted) blocking nets: expect this to take 15 min
deselect_obj -all; select_obj [list $n1 $n2]
route_design -no_placement_check

########################################################################
# bad patch wire M4
puts "@file_info Fixing M4 patch wire, should take about 15 minutes"

set n {net:GarnetSOC_pad_frame/core_u_proc_tlx/proc_subsys_dma0_upl330_engine_upl330_lsq_upl330_write_lsq_upl330_write_lsq_array_data_array\[15\][50]}

deselect_obj -all; select_obj $n
delete_routes -net $n

# Expect this to take like 15 minutes
deselect_obj -all; select_obj $n
route_design -no_placement_check



