create_constraint_mode -name functional -sdc_files results_syn/syn_out._default_constraint_mode_.sdc

create_library_set -name ss_0p72_m40c_lib_set -timing [list \
/tsmc16/TSMCHOME/digital/Front_End/timing_power_noise/NLDM/tcbn16ffcllbwp16p90_100a/tcbn16ffcllbwp16p90ssgnp0p72vm40c.lib \
/tsmc16/TSMCHOME/digital/Front_End/timing_power_noise/NLDM/tphn16ffcllgv18e_110c/tphn16ffcllgv18essgnp0p72v1p62vm40c.lib \
/sim/ajcars/mc/ts1n16ffcllsblvtc512x16m8s_130a/NLDM/ts1n16ffcllsblvtc512x16m8s_130a_ssgnp0p72vm40c.lib \
/sim/ajcars/mc/ts1n16ffcllsblvtc2048x32m8sw_130a/NLDM/ts1n16ffcllsblvtc2048x32m8sw_130a_ssgnp0p72vm40c.lib \
/sim/ajcars/mc/ts1n16ffcllsblvtc2048x64m8sw_130a/NLDM/ts1n16ffcllsblvtc2048x64m8sw_130a_ssgnp0p72vm40c.lib \
/tsmc16/TSMCHOME/digital/Front_End/timing_power_noise/NLDM/tcbn16ffcllbwp16p90pm_100a/tcbn16ffcllbwp16p90pmssgnp0p72vm40c.lib \
../Tile_PE/pnr.lib \
../Tile_MemCore/pnr.lib \
/tsmc16/TSMCHOME/digital/Front_End/timing_power_noise/NLDM/tcbn16ffcllbwp16p90lvt_100a/tcbn16ffcllbwp16p90lvtssgnp0p72vm40c.lib \
/tsmc16/TSMCHOME/digital/Front_End/timing_power_noise/NLDM/tcbn16ffcllbwp16p90ulvt_100a/tcbn16ffcllbwp16p90ulvtssgnp0p72vm40c.lib \
]

create_library_set -name ss_0p72_125c_lib_set -timing [list \
/tsmc16/TSMCHOME/digital/Front_End/timing_power_noise/NLDM/tcbn16ffcllbwp16p90_100a/tcbn16ffcllbwp16p90ssgnp0p72v125c.lib \
/tsmc16/TSMCHOME/digital/Front_End/timing_power_noise/NLDM/tphn16ffcllgv18e_110c/tphn16ffcllgv18essgnp0p72v1p62v125c.lib \
/sim/ajcars/mc/ts1n16ffcllsblvtc512x16m8s_130a/NLDM/ts1n16ffcllsblvtc512x16m8s_130a_ssgnp0p72v125c.lib \
/sim/ajcars/mc/ts1n16ffcllsblvtc2048x32m8sw_130a/NLDM/ts1n16ffcllsblvtc2048x32m8sw_130a_ssgnp0p72v125c.lib \
/sim/ajcars/mc/ts1n16ffcllsblvtc2048x64m8sw_130a/NLDM/ts1n16ffcllsblvtc2048x64m8sw_130a_ssgnp0p72v125c.lib \
/tsmc16/TSMCHOME/digital/Front_End/timing_power_noise/NLDM/tcbn16ffcllbwp16p90pm_100a/tcbn16ffcllbwp16p90pmssgnp0p72v125c.lib \
../Tile_PE/pnr.lib \
../Tile_MemCore/pnr.lib \
/tsmc16/TSMCHOME/digital/Front_End/timing_power_noise/NLDM/tcbn16ffcllbwp16p90lvt_100a/tcbn16ffcllbwp16p90lvtssgnp0p72v125c.lib \
/tsmc16/TSMCHOME/digital/Front_End/timing_power_noise/NLDM/tcbn16ffcllbwp16p90ulvt_100a/tcbn16ffcllbwp16p90ulvtssgnp0p72v125c.lib \
]

create_library_set -name ff_0p88_0c_lib_set -timing [list \
/tsmc16/TSMCHOME/digital/Front_End/timing_power_noise/NLDM/tcbn16ffcllbwp16p90_100a/tcbn16ffcllbwp16p90ffgnp0p88v0c.lib \
/sim/ajcars/mc/ts1n16ffcllsblvtc512x16m8s_130a/NLDM/ts1n16ffcllsblvtc512x16m8s_130a_ffgnp0p88v0c.lib \
/tsmc16/TSMCHOME/digital/Front_End/timing_power_noise/NLDM/tphn16ffcllgv18e_110c/tphn16ffcllgv18effgnp0p88v1p98v125c.lib \
/sim/ajcars/mc/ts1n16ffcllsblvtc2048x32m8sw_130a/NLDM/ts1n16ffcllsblvtc2048x32m8sw_130a_ffgnp0p88v0c.lib \
/sim/ajcars/mc/ts1n16ffcllsblvtc2048x64m8sw_130a/NLDM/ts1n16ffcllsblvtc2048x64m8sw_130a_ffgnp0p88v0c.lib \
/tsmc16/TSMCHOME/digital/Front_End/timing_power_noise/NLDM/tcbn16ffcllbwp16p90pm_100a/tcbn16ffcllbwp16p90pmffgnp0p88v0c.lib \
../Tile_PE/pnr.lib \
../Tile_MemCore/pnr.lib \
/tsmc16/TSMCHOME/digital/Front_End/timing_power_noise/NLDM/tcbn16ffcllbwp16p90lvt_100a/tcbn16ffcllbwp16p90lvtffgnp0p88v0c.lib \
/tsmc16/TSMCHOME/digital/Front_End/timing_power_noise/NLDM/tcbn16ffcllbwp16p90ulvt_100a/tcbn16ffcllbwp16p90ulvtffgnp0p88v0c.lib \
]


create_rc_corner -name max_rc_corner \
                          -pre_route_res 1.0 \
                          -pre_route_cap 1.0 \
                          -pre_route_clock_res 1.0 \
                          -pre_route_clock_cap 1.0 \
                          -post_route_res 1.0 \
                          -post_route_cap 1.0 \
                          -post_route_clock_res 1.0 \
                          -post_route_clock_cap 1.0 \
                          -post_route_cross_cap 1.0 \
                          -temperature -40 \
                          -qrc_tech /tsmc16/download/TECH16FFC/cworst/Tech/cworst_CCworst_T/qrcTechFile

create_rc_corner -name min_rc_corner \
                          -pre_route_res 1.0 \
                          -pre_route_cap 1.0 \
                          -pre_route_clock_res 1.0 \
                          -pre_route_clock_cap 1.0 \
                          -post_route_res 1.0 \
                          -post_route_cap 1.0 \
                          -post_route_clock_res 1.0 \
                          -post_route_clock_cap 1.0 \
                          -post_route_cross_cap 1.0 \
                          -temperature 0 \
                          -qrc_tech /tsmc16/download/TECH16FFC/cbest/Tech/cbest_CCbest_T/qrcTechFile


create_timing_condition -name ss_0p72_m40c_tc -library_sets ss_0p72_m40c_lib_set -opcond ssgnp0p72vm40c -opcond_library tcbn16ffcllbwp16p90ssgnp0p72vm40c
create_timing_condition -name ss_0p72_125c_tc -library_sets ss_0p72_125c_lib_set -opcond ssgnp0p72v125c -opcond_library tcbn16ffcllbwp16p90ssgnp0p72v125c
create_timing_condition -name ff_0p88_0c_tc   -library_sets ff_0p88_0c_lib_set   -opcond ffgnp0p88v0c   -opcond_library tcbn16ffcllbwp16p90ffgnp0p88v0c


create_delay_corner -name ss_0p72_m40c_dc -timing_condition ss_0p72_m40c_tc -rc_corner max_rc_corner
create_delay_corner -name ss_0p72_125c_dc -timing_condition ss_0p72_125c_tc -rc_corner max_rc_corner
create_delay_corner -name ff_0p88_0c_dc   -timing_condition ff_0p88_0c_tc   -rc_corner min_rc_corner

create_analysis_view -name ss_0p72_m40c -constraint_mode functional -delay_corner ss_0p72_m40c_dc
create_analysis_view -name ss_0p72_125c -constraint_mode functional -delay_corner ss_0p72_125c_dc
create_analysis_view -name ff_0p88_0c   -constraint_mode functional -delay_corner ff_0p88_0c_dc

set_analysis_view -setup [list ss_0p72_m40c ss_0p72_125c] -hold [list ss_0p72_m40c ss_0p72_125c ff_0p88_0c]
