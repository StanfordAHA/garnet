# ==============================================================================
# Include Paths for NIC400 IP
# ==============================================================================

set soc_inc_nic400 [concat \
  inputs/rtl/aham3soc_armip/logical/nic400_AhaIntegration/amib_master_CGRA_DATA/verilog \
  inputs/rtl/aham3soc_armip/logical/nic400_AhaIntegration/amib_master_CGRA_REG/verilog \
  inputs/rtl/aham3soc_armip/logical/nic400_AhaIntegration/amib_master_PERIPH/verilog \
  inputs/rtl/aham3soc_armip/logical/nic400_AhaIntegration/amib_master_SRAM0/verilog \
  inputs/rtl/aham3soc_armip/logical/nic400_AhaIntegration/amib_master_SRAM1/verilog \
  inputs/rtl/aham3soc_armip/logical/nic400_AhaIntegration/amib_master_SRAM2/verilog \
  inputs/rtl/aham3soc_armip/logical/nic400_AhaIntegration/amib_master_SRAM3/verilog \
  inputs/rtl/aham3soc_armip/logical/nic400_AhaIntegration/amib_master_TLX/verilog \
  inputs/rtl/aham3soc_armip/logical/nic400_AhaIntegration/amib_master_TLX_REG/verilog \
  inputs/rtl/aham3soc_armip/logical/nic400_AhaIntegration/asib_slave_CPU/verilog \
  inputs/rtl/aham3soc_armip/logical/nic400_AhaIntegration/asib_slave_DMA0/verilog \
  inputs/rtl/aham3soc_armip/logical/nic400_AhaIntegration/asib_slave_DMA1/verilog \
  inputs/rtl/aham3soc_armip/logical/nic400_AhaIntegration/busmatrix_bm0/verilog \
  inputs/rtl/aham3soc_armip/logical/nic400_AhaIntegration/cdc_blocks/verilog \
  inputs/rtl/aham3soc_armip/logical/nic400_AhaIntegration/default_slave_ds_1/verilog \
  inputs/rtl/aham3soc_armip/logical/nic400_AhaIntegration/ib_master_CGRA_DATA_ib/verilog \
  inputs/rtl/aham3soc_armip/logical/nic400_AhaIntegration/ib_master_CGRA_REG_ib/verilog \
  inputs/rtl/aham3soc_armip/logical/nic400_AhaIntegration/ib_master_PERIPH_ib/verilog \
  inputs/rtl/aham3soc_armip/logical/nic400_AhaIntegration/ib_master_TLX_REG_ib/verilog \
  inputs/rtl/aham3soc_armip/logical/nic400_AhaIntegration/ib_master_TLX_ib/verilog \
  inputs/rtl/aham3soc_armip/logical/nic400_AhaIntegration/ib_slave_CPU_ib/verilog \
  inputs/rtl/aham3soc_armip/logical/nic400_AhaIntegration/reg_slice/verilog \
  inputs/rtl/aham3soc_armip/logical/nic400_AhaIntegration/nic400/verilog/Axi \
  inputs/rtl/aham3soc_armip/logical/nic400_AhaIntegration/nic400/verilog/Ahb \
]
