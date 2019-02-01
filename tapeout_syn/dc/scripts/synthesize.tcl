set_app_var search_path [list \
$::env(SAED32_28_PDK) \
$::env(SAED32_PATH)]

set_app_var target_library [list \
$::env(SAED32_PATH)/lib/stdcell_rvt/db_ccs/saed32rvt_tt1p05vn40c.db \
$::env(SAED32_PATH)/lib/stdcell_rvt/db_ccs/saed32rvt_dlvl_tt1p05vn40c_i1p05v.db \
$::env(SAED32_PATH)/lib/stdcell_rvt/db_ccs/saed32rvt_pg_tt1p05vn40c.db \
$::env(SAED32_PATH)/lib/stdcell_rvt/db_ccs/saed32rvt_ulvl_tt1p05vn40c_i1p05v.db]

set_app_var symbol_library $::env(SAED32_28_PDK)/sym_libs/snpsDefTechLib/tech.db

set_app_var link_library [list \
{*}$target_library \
$::env(SAED32_PATH)/lib/sram/db_ccs/saed32sram_tt1p05vn40c.db]

set design_name $::env(DESIGN)

set report_dir ./reports

sh mkdir -p $report_dir

define_design_lib WORK -path ./WORK

#create_mw_lib -technology $::env(SAED32_PATH)/tech/milkyway/saed32nm_1p9m_mw.tf \
#-mw_reference_library [list \
#$::env(SAED32_PATH)/lib/stdcell_rvt/milkyway/saed32nm_rvt_1p9m \
#$::env(SAED32_PATH)/lib/sram/milkyway/SRAM32NM] \
#$report_dir/$design_name -open


#Read in the RTL
read_file -top $design_name -autoread [glob -directory ../../../rtl -type f *.v *.sv]
current_design $design_name

link

#Constraints
source -verbose "../../scripts/constraints_${design_name}.tcl"


ungroup -all

check_design > $report_dir/$design_name.chk1

report_ultra_optimization
report_compile_options

link
compile_ultra -gate_clock              -scan -no_seq_output_inversion -no_autoungroup 
compile_ultra -gate_clock -incremental -scan -no_seq_output_inversion -no_autoungroup 

# change_names -rule verilog -hierarchy

check_design > $report_dir/$design_name.chk2

report_timing -in -net -transition_time  -capacitance  -significant_digits  4 -attributes  -nosplit -path full_clock -delay max -nworst 1 -max_paths 10 > $report_dir/$design_name.time

write -format verilog -hierarchy -output ./$design_name.sv
report_qor > $report_dir/$design_name.qor.rpt
report_power > $report_dir/$design_name.power.top.rpt
report_area > $report_dir/$design_name.area.rpt
report_power -hierarchy -levels 3 >  $report_dir/$design_name.power.rpt
write -format ddc -hier -out ./$design_name.ddc;

quit

