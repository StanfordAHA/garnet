#!/bin/bash
# ==============================================================================
# loads SOC design files (RTL)
# ==============================================================================
# Cortex-M3 Files
soc_cm3_files=(
  aha-arm-soc-june-2019/components/cortex-m3/cm3_wic/verilog/*.v 
  aha-arm-soc-june-2019/components/cortex-m3/cm3_itm/verilog/*.v
  aha-arm-soc-june-2019/components/cortex-m3/cm3_tpiu/verilog/*.v
  aha-arm-soc-june-2019/components/cortex-m3/cm3_fpb/verilog/*.v 
  aha-arm-soc-june-2019/components/cortex-m3/cm3_mpu/verilog/*.v 
  aha-arm-soc-june-2019/components/cortex-m3/cm3_dwt/verilog/*.v 
  aha-arm-soc-june-2019/components/cortex-m3/cm3_nvic/verilog/*.v
  aha-arm-soc-june-2019/components/cortex-m3/cm3_dpu/verilog/*.v
  aha-arm-soc-june-2019/components/cortex-m3/cm3_dap_ahb_ap/verilog/*.v
  aha-arm-soc-june-2019/components/cortex-m3/cm3_bus_matrix/verilog/*.v
  aha-arm-soc-june-2019/components/cortex-m3/dapswjdp/verilog/*.v
  aha-arm-soc-june-2019/components/cortex-m3/cortexm3/verilog/*.v
  aha-arm-soc-june-2019/components/cortex-m3/models/cells/*.v 
)

# CMSDK Files
soc_cmdk_files=(
  aha-arm-soc-june-2019/components/cmsdk/cmsdk_apb_dualtimers/verilog/*.v 
  aha-arm-soc-june-2019/components/cmsdk/cmsdk_apb_uart/verilog/*.v
  aha-arm-soc-june-2019/components/cmsdk/cmsdk_apb_watchdog/verilog/*.v
  aha-arm-soc-june-2019/components/cmsdk/cmsdk_apb3_eg_slave/verilog/*.v
  aha-arm-soc-june-2019/components/cmsdk/cmsdk_apb_slave_mux/verilog/*.v
)

# RTC (Real Time Clock) Files
soc_rtc_files=(
  aha-arm-soc-june-2019/components/rtc/*.v
)

# SRAMs
soc_sram_files=(
  aha-arm-soc-june-2019/components/sram/common/*.v
  aha-arm-soc-june-2019/components/sram/common/axi-sram/*.v
  aha-arm-soc-june-2019/components/sram/synthesis/*.v
)

# STDCELL Wrapper Files
soc_stdcell_wrp_files=(
  aha-arm-soc-june-2019/components/std-cells/synthesis/*.v
)

# SOC SDK Files
soc_sdk_files=(
  aha-arm-soc-june-2019/components/socsdk/*.v
)

# SoC Controller Files
soc_ctrl_files=(
  aha-arm-soc-june-2019/components/soc_controller/*.v
)

# Integration Files
soc_integration_files=(
  aha-arm-soc-june-2019/integration/*.v
)

# PL330 DMA Files
soc_dma_files=(
  aha-arm-soc-june-2019/components/nic450/logical/DMA330_aha/logical/pl330_dma_aha/pl330_dma_aha/verilog/*.v
  aha-arm-soc-june-2019/components/nic450/logical/DMA330_aha/logical/pl330_dma_aha/pl330_axi_aha/verilog/*.v
  aha-arm-soc-june-2019/components/nic450/logical/DMA330_aha/logical/pl330_dma_aha/pl330_icache_aha/verilog/*.v
  aha-arm-soc-june-2019/components/nic450/logical/DMA330_aha/logical/pl330_dma_aha/pl330_lsq_aha/verilog/*.v
  aha-arm-soc-june-2019/components/nic450/logical/DMA330_aha/logical/pl330_dma_aha/pl330_pipeline_aha/verilog/*.v
  aha-arm-soc-june-2019/components/nic450/logical/DMA330_aha/logical/pl330_dma_aha/pl330_mfifo_aha/verilog/*.v
  aha-arm-soc-june-2019/components/nic450/logical/DMA330_aha/logical/pl330_dma_aha/pl330_engine_aha/verilog/*.v
  aha-arm-soc-june-2019/components/nic450/logical/DMA330_aha/logical/pl330_dma_aha/pl330_merge_buffer_aha/verilog/*.v
  aha-arm-soc-june-2019/components/nic450/logical/DMA330_aha/logical/pl330_dma_aha/pl330_periph_aha/verilog/*.v
)

# TLX-400 Files
bash ./tlx_design_files.sh

# NIC-400 Files
bash ./nic400_design_files.sh

# CGRA-SoC Interface Files
soc_cgra_if_files=(
  aha-arm-soc-june-2019/components/cgra/axi_to_cgra_data/*.v
  aha-arm-soc-june-2019/components/cgra/axi_to_cgra_reg/*.v
)

# All SoC Files
soc_design_files=(
  $soc_cm3_files
  $soc_cmdk_files
  $soc_rtc_files
  $soc_sram_files
  $soc_stdcell_wrp_files
  $soc_sdk_files
  $soc_integration_files
  $soc_dma_files
  $soc_tlx_files
  $soc_nic400_files
  $soc_cgra_if_files
  $soc_ctrl_files
)
