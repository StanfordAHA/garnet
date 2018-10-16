create_constraint_mode -name functional -sdc_files results_syn/syn_out._default_constraint_mode_.sdc

create_library_set -name ss_0p72_m40c_lib_set -timing "/tsmc16/TSMCHOME/digital/Front_End/timing_power_noise/NLDM/tcbn16ffcllbwp16p90_100a/tcbn16ffcllbwp16p90ssgnp0p72vm40c.lib /sim/nikhil3/mem_compile/130a/TSMCHOME/sram/Compiler/tsn16ffcllhdspsbsram_20131200_130a/ts1n16ffcllsblvtc512x16m8s_130a/NLDM/ts1n16ffcllsblvtc512x16m8s_130a_ssgnp0p72vm40c.lib"

create_library_set -name ss_0p72_125c_lib_set -timing "/tsmc16/TSMCHOME/digital/Front_End/timing_power_noise/NLDM/tcbn16ffcllbwp16p90_100a/tcbn16ffcllbwp16p90ssgnp0p72v125c.lib /sim/nikhil3/mem_compile/130a/TSMCHOME/sram/Compiler/tsn16ffcllhdspsbsram_20131200_130a/ts1n16ffcllsblvtc512x16m8s_130a/NLDM/ts1n16ffcllsblvtc512x16m8s_130a_ssgnp0p72v125c.lib"

create_library_set -name ff_0p88_0c_lib_set -timing "/tsmc16/TSMCHOME/digital/Front_End/timing_power_noise/NLDM/tcbn16ffcllbwp16p90_100a/tcbn16ffcllbwp16p90ffgnp0p88v0c.lib /sim/nikhil3/mem_compile/130a/TSMCHOME/sram/Compiler/tsn16ffcllhdspsbsram_20131200_130a/ts1n16ffcllsblvtc512x16m8s_130a/NLDM/ts1n16ffcllsblvtc512x16m8s_130a_ffgnp0p88v0c.lib"


create_rc_corner -name max_rc_corner \
                          -preRoute_res 1.0 \
                          -preRoute_cap 1.0 \
                          -preRoute_clkres 1.0 \
                          -preRoute_clkcap 1.0 \
                          -postRoute_res 1.0 \
                          -postRoute_cap 1.0 \
                          -postRoute_clkres 1.0 \
                          -postRoute_clkcap 1.0 \
                          -postRoute_xcap 1.0 \
                          -T -40 \
                          -qx_tech_file /tsmc16/download/TECH16FFC/cworst/Tech/cworst_CCworst_T/qrcTechFile

create_rc_corner -name min_rc_corner \
                          -preRoute_res 1.0 \
                          -preRoute_cap 1.0 \
                          -preRoute_clkres 1.0 \
                          -preRoute_clkcap 1.0 \
                          -postRoute_res 1.0 \
                          -postRoute_cap 1.0 \
                          -postRoute_clkres 1.0 \
                          -postRoute_clkcap 1.0 \
                          -postRoute_xcap 1.0 \
                          -T 0 \
                          -qx_tech_file /tsmc16/download/TECH16FFC/cbest/Tech/cbest_CCbest_T/qrcTechFile

create_delay_corner -name ss_0p72_m40c_dc -library_set ss_0p72_m40c_lib_set -rc_corner max_rc_corner
create_delay_corner -name ss_0p72_125c_dc -library_set ss_0p72_125c_lib_set -rc_corner max_rc_corner
create_delay_corner -name ff_0p88_0c_dc   -library_set ff_0p88_0c_lib_set   -rc_corner min_rc_corner

create_analysis_view -name ss_0p72_m40c -constraint_mode functional -delay_corner ss_0p72_m40c_dc
create_analysis_view -name ss_0p72_125c -constraint_mode functional -delay_corner ss_0p72_125c_dc
create_analysis_view -name ff_0p88_0c   -constraint_mode functional -delay_corner ff_0p88_0c_dc

set_analysis_view -setup [list ss_0p72_m40c ss_0p72_125c] -hold [list ss_0p72_m40c ss_0p72_125c ff_0p88_0c]
#set_default_view -setup ss_0p72_m40c -hold ff_0p88_0c
