# ==============================================================================
# loads SOC design files (RTL)
# ==============================================================================
# Cortex-M3 Files
set soc_cm3_files [concat [
  glob -nocomplain -directory inputs/rtl/aham3soc_armip/logical/cortex-m3/cm3_wic/verilog -types f *.v] [
  glob -nocomplain -directory inputs/rtl/aham3soc_armip/logical/cortex-m3/cm3_itm/verilog -types f *.v] [
  glob -nocomplain -directory inputs/rtl/aham3soc_armip/logical/cortex-m3/cm3_tpiu/verilog -types f *.v] [
  glob -nocomplain -directory inputs/rtl/aham3soc_armip/logical/cortex-m3/cm3_fpb/verilog -types f *.v] [
  glob -nocomplain -directory inputs/rtl/aham3soc_armip/logical/cortex-m3/cm3_mpu/verilog -types f *.v] [
  glob -nocomplain -directory inputs/rtl/aham3soc_armip/logical/cortex-m3/cm3_dwt/verilog -types f *.v] [
  glob -nocomplain -directory inputs/rtl/aham3soc_armip/logical/cortex-m3/cm3_nvic/verilog -types f *.v] [
  glob -nocomplain -directory inputs/rtl/aham3soc_armip/logical/cortex-m3/cm3_dpu/verilog -types f *.v] [
  glob -nocomplain -directory inputs/rtl/aham3soc_armip/logical/cortex-m3/cm3_dap_ahb_ap/verilog -types f *.v] [
  glob -nocomplain -directory inputs/rtl/aham3soc_armip/logical/cortex-m3/cm3_bus_matrix/verilog -types f *.v] [
  glob -nocomplain -directory inputs/rtl/aham3soc_armip/logical/cortex-m3/dapswjdp/verilog -types f *.v] [
  glob -nocomplain -directory inputs/rtl/aham3soc_armip/logical/cortex-m3/cortexm3/verilog -types f *.v] [
  glob -nocomplain -directory inputs/rtl/aham3soc_armip/logical/cortex-m3/cortexm3_integration/verilog -types f *.v] [
  glob -nocomplain -directory inputs/rtl/aham3soc_armip/logical/cortex-m3/models/cells -types f *.v ] ]

# CMSDK Files
set soc_cmdk_files [concat [
  glob -nocomplain -directory inputs/rtl/aham3soc_armip/logical/cmsdk/cmsdk_apb_uart/verilog -types f *.v] [
  glob -nocomplain -directory inputs/rtl/aham3soc_armip/logical/cmsdk/cmsdk_apb_watchdog/verilog -types f *.v] [
  glob -nocomplain -directory inputs/rtl/aham3soc_armip/logical/cmsdk/cmsdk_ahb_to_apb/verilog -types f *.v] [
  glob -nocomplain -directory inputs/rtl/aham3soc_armip/logical/cmsdk/cmsdk_apb_timer/verilog -types f *.v] [
  glob -nocomplain -directory inputs/rtl/aham3soc_armip/logical/cmsdk/cmsdk_ahb_to_sram/verilog -types f *.v] [
  glob -nocomplain -directory inputs/rtl/aham3soc_armip/logical/cmsdk/cmsdk_ahb_eg_slave/verilog -types f *.v] [
  glob -nocomplain -directory inputs/rtl/aham3soc_armip/logical/AhaPeriphAhbMtx/verilog/AhaPeriphAhbMtx -types f *.v ] ]

# AXI SRAM Interface Converter
set soc_sram_if_files [ glob -nocomplain -directory inputs/rtl/aham3soc_armip/logical/if_converters/axi_sram_if -types f *.v]

# Integration Files
set soc_integration_files [concat [
  glob -nocomplain -directory inputs/rtl/aham3soc/hardware/logical/AhaCM3CodeRegionIntegration/verilog -types f *.v] [
  glob -nocomplain -directory inputs/rtl/aham3soc/hardware/logical/AhaCM3Integration/verilog -types f *.v] [
  glob -nocomplain -directory inputs/rtl/aham3soc/hardware/logical/AhaDmaIntegration/verilog -types f *.v] [
  glob -nocomplain -directory inputs/rtl/aham3soc/hardware/logical/AhaGarnetIntegration/verilog -types f *.v] [
  glob -nocomplain -directory inputs/rtl/aham3soc/hardware/logical/AhaGarnetSoC/verilog -types f *.v] [
  glob -nocomplain -directory inputs/rtl/aham3soc/hardware/logical/AhaMemIntegration/verilog -types f *.v] [
  glob -nocomplain -directory inputs/rtl/aham3soc/hardware/logical/AhaPeripherals/verilog -types f *.v] [
  glob -nocomplain -directory inputs/rtl/aham3soc/hardware/logical/AhaPlatformController/verilog -types f *.v] [
  glob -nocomplain -directory inputs/rtl/aham3soc/hardware/logical/AhaPlatformController/rdl/verilog -types f *.v] [
  glob -nocomplain -directory inputs/rtl/aham3soc/hardware/logical/AhaSoCPartialIntegration/verilog -types f *.v] [
  glob -nocomplain -directory inputs/rtl/aham3soc/hardware/logical/AhaTlxIntegration/verilog -types f *.v] [
  glob -nocomplain -directory inputs/rtl/aham3soc/hardware/logical/AhaTlxIntegration/rdl/verilog -types f *.v] [
  glob -nocomplain -directory inputs/rtl/aham3soc/hardware/logical/AhaStdCells/asic/verilog -types f *.v]]

# PL330 DMA Files
set soc_dma_files [concat [
  glob -nocomplain -directory inputs/rtl/aham3soc_armip/logical/DMA330_AhaIntegration/logical/pl330_dma_AhaIntegration/pl330_dma_AhaIntegration/verilog -types f *.v] [
  glob -nocomplain -directory inputs/rtl/aham3soc_armip/logical/DMA330_AhaIntegration/logical/pl330_dma_AhaIntegration/pl330_axi_AhaIntegration/verilog -types f *.v] [
  glob -nocomplain -directory inputs/rtl/aham3soc_armip/logical/DMA330_AhaIntegration/logical/pl330_dma_AhaIntegration/pl330_icache_AhaIntegration/verilog -types f *.v] [
  glob -nocomplain -directory inputs/rtl/aham3soc_armip/logical/DMA330_AhaIntegration/logical/pl330_dma_AhaIntegration/pl330_lsq_AhaIntegration/verilog -types f *.v] [
  glob -nocomplain -directory inputs/rtl/aham3soc_armip/logical/DMA330_AhaIntegration/logical/pl330_dma_AhaIntegration/pl330_pipeline_AhaIntegration/verilog -types f *.v] [
  glob -nocomplain -directory inputs/rtl/aham3soc_armip/logical/DMA330_AhaIntegration/logical/pl330_dma_AhaIntegration/pl330_mfifo_AhaIntegration/verilog -types f *.v] [
  glob -nocomplain -directory inputs/rtl/aham3soc_armip/logical/DMA330_AhaIntegration/logical/pl330_dma_AhaIntegration/pl330_engine_AhaIntegration/verilog -types f *.v] [
  glob -nocomplain -directory inputs/rtl/aham3soc_armip/logical/DMA330_AhaIntegration/logical/pl330_dma_AhaIntegration/pl330_merge_buffer_AhaIntegration/verilog -types f *.v] [
  glob -nocomplain -directory inputs/rtl/aham3soc_armip/logical/DMA330_AhaIntegration/logical/pl330_dma_AhaIntegration/pl330_periph_AhaIntegration/verilog -types f *.v]]

# TLX-400 Files
source inputs/rtl-scripts/tlx_design_files.tcl

# NIC-400 Files
source inputs/rtl-scripts/nic400_design_files.tcl

# All SoC Files
set soc_design_files [concat \
  $soc_cm3_files \
  $soc_cmdk_files \
  $soc_sram_if_files \
  $soc_integration_files \
  $soc_dma_files \
  $soc_tlx_files \
]


set soc_design_files [concat \
  $soc_cm3_files \
  $soc_cmdk_files \
  $soc_sram_if_files \
  $soc_integration_files \
  $soc_dma_files \
  $soc_tlx_files \
  $soc_nic400_files \
]
