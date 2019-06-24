
set gds_files [list \
/tsmc16/TSMCHOME/digital/Back_End/gds/tcbn16ffcllbwp16p90_100a/tcbn16ffcllbwp16p90.gds \
/tsmc16/TSMCHOME/digital/Back_End/gds/tpbn16v_090a/fc/fc_lf_bu/APRDL/tpbn16v.gds \
/tsmc16/TSMCHOME/digital/Back_End/gds/tphn16ffcllgv18e_110e/mt_1/9m/9M_2XA1XD_H_3XE_VHV_2Z/tphn16ffcllgv18e.gds \
/tsmc16/pdk/2016.09.15_MOSIS/FFC/T-N16-CL-DR-032/N16_DTCD_library_kit_20160111/N16_DTCD_library_kit_20160111/gds/N16FF_Phantom_v1d0_1a_20140707.gds \
/sim/ajcars/mc/ts1n16ffcllsblvtc512x16m8s_130a/GDSII/ts1n16ffcllsblvtc512x16m8s_130a_m4xdh.gds \
/sim/ajcars/mc/ts1n16ffcllsblvtc2048x64m8sw_130a/GDSII/ts1n16ffcllsblvtc2048x64m8sw_130a_m4xdh.gds \
/tsmc16/download/TECH16FFC/ICOVL/43_ICOVL_cells_FFC.gds \
/home/ajcars/seal_ring/N16_SR_B_1KX1K_DPO_DOD_FFC_5x5.gds \
../Tile_PE/pnr.gds \
../Tile_MemCore/pnr.gds \
/sim/ajcars/aha-arm-soc-june-2019/components/butterphy/butterphy_top.gds
]


streamOut final.gds -uniquifyCellNames -mode ALL -merge ${gds_files} -mapFile /tsmc16/pdk/latest/pnr/innovus/PR_tech/Cadence/GdsOutMap/gdsout_2Xa1Xd_h_3Xe_vhv_2Z_1.2a.map -units 1000

saveNetlist pnr.lvs.v -includePowerGround -excludeLeafCell -includeBumpCell -phys

redirect pnr.setup.timing {report_timing -max_paths 1000 -nworst 20}
setAnalysisMode -checkType hold
redirect pnr.hold.timing {report_timing -max_paths 1000 -nworst 20}
