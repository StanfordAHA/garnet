# ==============================================================================
# Include Paths for SoC
# ==============================================================================

# Cortex-M3 Include Paths
set soc_inc_cm3 [concat \
  inputs/rtl/components/cortex-m3/cm3_tpiu/verilog \
  inputs/rtl/components/cortex-m3/cm3_dpu/verilog \
  inputs/rtl/components/cortex-m3/cm3_nvic/verilog \
  inputs/rtl/components/cortex-m3/cm3_bus_matrix/verilog \
  inputs/rtl/components/cortex-m3/cm3_dap_ahb_ap/verilog \
  inputs/rtl/components/cortex-m3/dapswjdp/verilog \
  inputs/rtl/components/cortex-m3/cm3_mpu/verilog \
  inputs/rtl/components/cortex-m3/cm3_dwt/verilog \
  inputs/rtl/components/cortex-m3/cm3_fpb/verilog \
  inputs/rtl/components/cortex-m3/cm3_lic_defs/verilog ]

# CMSDK Include Paths
set soc_inc_cmsdk [concat \
  inputs/rtl/components/cmsdk/cmsdk_apb_dualtimers/verilog \
  inputs/rtl/components/cmsdk/cmsdk_apb_dualtimers/verilog \
  inputs/rtl/components/cmsdk/cmsdk_apb_watchdog/verilog ]

# RTC Include Paths
set soc_inc_rtc [concat \
    inputs/rtl/components/rtc ]

# PL330 DMA Include Paths
set soc_inc_dma [concat \
  inputs/rtl/components/nic450/logical/DMA330_aha/logical/pl330_dma_aha/pl330_dma_aha/verilog/BP148-MN-22001 \
  inputs/rtl/components/nic450/logical/DMA330_aha/logical/pl330_dma_aha/pl330_dma_aha/verilog ]

# TLX-400 Include Paths
source inputs/rtl-scripts/tlx_include_paths.tcl

# NIC-400 Include Paths
source inputs/rtl-scripts/nic400_include_paths.tcl

# All SoC Include Paths
#set_attr init_hdl_search_path [concat \
#  $soc_inc_cm3 \
#  $soc_inc_cmsdk \
#  $soc_inc_rtc \
#  $soc_inc_dma \
#  $soc_inc_tlx \
#  $soc_inc_nic400]

lappend search_path [concat \
  $soc_inc_cm3 \
  $soc_inc_cmsdk \
  $soc_inc_rtc \
  $soc_inc_dma \
  $soc_inc_tlx \
  $soc_inc_nic400]
