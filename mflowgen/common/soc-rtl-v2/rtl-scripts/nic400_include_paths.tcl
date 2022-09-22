# ==============================================================================
# Include Paths for NIC400 IP
# ==============================================================================

set soc_inc_nic400 [concat \
    inputs/rtl/aham3soc_armip/logical/nic400_OnyxIntegration/nic400/verilog \
    inputs/rtl/aham3soc_armip/logical/nic400_OnyxIntegration/amib_M_AHB_PERIPH/verilog \
    inputs/rtl/aham3soc_armip/logical/nic400_OnyxIntegration/amib_M_AHB_TLX_REG/verilog \
    inputs/rtl/aham3soc_armip/logical/nic400_OnyxIntegration/amib_M_AHB_XGCD/verilog \
    inputs/rtl/aham3soc_armip/logical/nic400_OnyxIntegration/amib_M_AXI_CGRA_DATA/verilog \
    inputs/rtl/aham3soc_armip/logical/nic400_OnyxIntegration/amib_M_AXI_CGRA_REG/verilog \
    inputs/rtl/aham3soc_armip/logical/nic400_OnyxIntegration/amib_M_AXI_SRAM0/verilog \
    inputs/rtl/aham3soc_armip/logical/nic400_OnyxIntegration/amib_M_AXI_SRAM1/verilog \
    inputs/rtl/aham3soc_armip/logical/nic400_OnyxIntegration/amib_M_AXI_SRAM2/verilog \
    inputs/rtl/aham3soc_armip/logical/nic400_OnyxIntegration/amib_M_AXI_SRAM3/verilog \
    inputs/rtl/aham3soc_armip/logical/nic400_OnyxIntegration/amib_M_AXI_TLX_DATA/verilog \
    inputs/rtl/aham3soc_armip/logical/nic400_OnyxIntegration/amib_M_AXI_XGCD0/verilog \
    inputs/rtl/aham3soc_armip/logical/nic400_OnyxIntegration/amib_M_AXI_XGCD1/verilog \
    inputs/rtl/aham3soc_armip/logical/nic400_OnyxIntegration/asib_S_AHB_CPU/verilog \
    inputs/rtl/aham3soc_armip/logical/nic400_OnyxIntegration/asib_S_AXI_DMA0/verilog \
    inputs/rtl/aham3soc_armip/logical/nic400_OnyxIntegration/asib_S_AXI_DMA1/verilog \
    inputs/rtl/aham3soc_armip/logical/nic400_OnyxIntegration/busmatrix_bm0/verilog \
    inputs/rtl/aham3soc_armip/logical/nic400_OnyxIntegration/busmatrix_bm1/verilog \
    inputs/rtl/aham3soc_armip/logical/nic400_OnyxIntegration/busmatrix_bm2/verilog \
    inputs/rtl/aham3soc_armip/logical/nic400_OnyxIntegration/cdc_blocks/verilog \
    inputs/rtl/aham3soc_armip/logical/nic400_OnyxIntegration/default_slave_ds_4/verilog \
    inputs/rtl/aham3soc_armip/logical/nic400_OnyxIntegration/ib_M_AHB_PERIPH_ib/verilog \
    inputs/rtl/aham3soc_armip/logical/nic400_OnyxIntegration/ib_M_AHB_TLX_REG_ib/verilog \
    inputs/rtl/aham3soc_armip/logical/nic400_OnyxIntegration/ib_M_AHB_XGCD_ib/verilog \
    inputs/rtl/aham3soc_armip/logical/nic400_OnyxIntegration/ib_M_AXI_CGRA_DATA_ib/verilog \
    inputs/rtl/aham3soc_armip/logical/nic400_OnyxIntegration/ib_M_AXI_CGRA_REG_ib/verilog \
    inputs/rtl/aham3soc_armip/logical/nic400_OnyxIntegration/ib_M_AXI_TLX_DATA_ib/verilog \
    inputs/rtl/aham3soc_armip/logical/nic400_OnyxIntegration/ib_S_AHB_CPU_ib/verilog \
    inputs/rtl/aham3soc_armip/logical/nic400_OnyxIntegration/ib_ib3/verilog \
    inputs/rtl/aham3soc_armip/logical/nic400_OnyxIntegration/reg_slice/verilog \
    inputs/rtl/aham3soc_armip/logical/nic400_OnyxIntegration/nic400/verilog/Axi \
    inputs/rtl/aham3soc_armip/logical/nic400_OnyxIntegration/nic400/verilog/Ahb \
]
