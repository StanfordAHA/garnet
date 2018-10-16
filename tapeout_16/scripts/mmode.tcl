create_library_set -name default_library_set -timing [list \
/tsmc16/TSMCHOME/digital/Front_End/timing_power_noise/NLDM/tcbn16ffcllbwp16p90_100a/tcbn16ffcllbwp16p90ssgnp0p72vm40c.lib \
/tsmc16/TSMCHOME/digital/Front_End/timing_power_noise/NLDM/tphn16ffcllgv18e_110c/tphn16ffcllgv18essgnp0p72v1p62vm40c.lib \
../memory_tile_unq1/pnr.lib \
../pe_tile_new_unq1/pnr.lib \
]

create_timing_condition -library_sets default_library_set -name default_timing_condition -opcond ssgnp0p72vm40c  -opcond_library tcbn16ffcllbwp16p90ssgnp0p72vm40c

create_rc_corner -name _default_rc_corner_ -T -40.0 -qrc_tech /tsmc16/download/TECH16FFC/cworst/Tech/cworst_CCworst_T/qrcTechFile

create_delay_corner -name _default_delay_corner_ -late_timing_condition default_timing_condition -late_rc_corner _default_rc_corner_ -early_timing_condition default_timing_condition -early_rc_corner _default_rc_corner_

create_constraint_mode -name _default_constraint_mode_ -sdc_files {results_syn/syn_out._default_constraint_mode_.sdc} 
 
create_analysis_view -name _default_view_  -constraint_mode _default_constraint_mode_ -delay_corner _default_delay_corner_
 
set_analysis_view -setup _default_view_  -hold _default_view_
 
