# ==============================================================================
# Include Paths for SoC
# ==============================================================================

# Cortex-M3 Include Paths
set soc_inc_cm3 [concat \
  rtl/components/cortex-m3/cm3_tpiu/verilog \
  rtl/components/cortex-m3/cm3_dpu/verilog \
  rtl/components/cortex-m3/cm3_nvic/verilog \
  rtl/components/cortex-m3/cm3_bus_matrix/verilog \
  rtl/components/cortex-m3/cm3_dap_ahb_ap/verilog \
  rtl/components/cortex-m3/dapswjdp/verilog \
  rtl/components/cortex-m3/cm3_mpu/verilog \
  rtl/components/cortex-m3/cm3_dwt/verilog \
  rtl/components/cortex-m3/cm3_fpb/verilog \
  rtl/components/cortex-m3/cm3_lic_defs/verilog ]

# CMSDK Include Paths
set soc_inc_cmsdk [concat \
  rtl/components/cmsdk/cmsdk_apb_dualtimers/verilog \
  rtl/components/cmsdk/cmsdk_apb_dualtimers/verilog \
  rtl/components/cmsdk/cmsdk_apb_watchdog/verilog ]

# RTC Include Paths
set soc_inc_rtc [concat \
    rtl/components/rtc ]

# PL330 DMA Include Paths
set soc_inc_dma [concat \
  rtl/components/nic450/logical/DMA330_aha/logical/pl330_dma_aha/pl330_dma_aha/verilog/BP148-MN-22001 \
  rtl/components/nic450/logical/DMA330_aha/logical/pl330_dma_aha/pl330_dma_aha/verilog ]

# TLX-400 Include Paths
source scripts/tlx_include_paths.tcl

# NIC-400 Include Paths
source scripts/nic400_include_paths.tcl

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
