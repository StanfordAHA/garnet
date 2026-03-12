# ==============================================================================
# Include Paths for NIC400 IP
# ==============================================================================
# we used to have this:
#     ib_M_AXI_CGRA_DATA_ib/verilog \
# but now, it disappears to be in the nic400 directory
# and instead, we have this new directory:
#     ib_ib2/verilog
#
set soc_inc_nic400 [concat \
    inputs/rtl/aham3soc_armip/logical/nic400_ZirconIntegration/nic400/verilog \
    inputs/rtl/aham3soc_armip/logical/nic400_ZirconIntegration/amib_M_AHB_PERIPH/verilog \
    inputs/rtl/aham3soc_armip/logical/nic400_ZirconIntegration/amib_M_AHB_TLX_REG/verilog \
    inputs/rtl/aham3soc_armip/logical/nic400_ZirconIntegration/amib_M_AXI_CGRA_DATA/verilog \
    inputs/rtl/aham3soc_armip/logical/nic400_ZirconIntegration/amib_M_AXI_CGRA_REG/verilog \
    inputs/rtl/aham3soc_armip/logical/nic400_ZirconIntegration/amib_M_AXI_SRAM0/verilog \
    inputs/rtl/aham3soc_armip/logical/nic400_ZirconIntegration/amib_M_AXI_SRAM1/verilog \
    inputs/rtl/aham3soc_armip/logical/nic400_ZirconIntegration/amib_M_AXI_SRAM2/verilog \
    inputs/rtl/aham3soc_armip/logical/nic400_ZirconIntegration/amib_M_AXI_SRAM3/verilog \
    inputs/rtl/aham3soc_armip/logical/nic400_ZirconIntegration/amib_M_AXI_TLX_DATA/verilog \
    inputs/rtl/aham3soc_armip/logical/nic400_ZirconIntegration/amib_M_AXI_MU_REG/verilog \
    inputs/rtl/aham3soc_armip/logical/nic400_ZirconIntegration/asib_S_AHB_CPU/verilog \
    inputs/rtl/aham3soc_armip/logical/nic400_ZirconIntegration/asib_S_AXI_DMA0/verilog \
    inputs/rtl/aham3soc_armip/logical/nic400_ZirconIntegration/asib_S_AXI_DMA1/verilog \
    inputs/rtl/aham3soc_armip/logical/nic400_ZirconIntegration/busmatrix_bm0/verilog \
    inputs/rtl/aham3soc_armip/logical/nic400_ZirconIntegration/busmatrix_bm1/verilog \
    inputs/rtl/aham3soc_armip/logical/nic400_ZirconIntegration/cdc_blocks/verilog \
    inputs/rtl/aham3soc_armip/logical/nic400_ZirconIntegration/default_slave_ds_3/verilog \
    inputs/rtl/aham3soc_armip/logical/nic400_ZirconIntegration/ib_M_AHB_PERIPH_ib/verilog \
    inputs/rtl/aham3soc_armip/logical/nic400_ZirconIntegration/ib_M_AHB_TLX_REG_ib/verilog \
    inputs/rtl/aham3soc_armip/logical/nic400_ZirconIntegration/ib_ib2/verilog \
    inputs/rtl/aham3soc_armip/logical/nic400_ZirconIntegration/ib_M_AXI_CGRA_DATA_ib/verilog \
    inputs/rtl/aham3soc_armip/logical/nic400_ZirconIntegration/ib_S_AHB_CPU_ib/verilog \
    inputs/rtl/aham3soc_armip/logical/nic400_ZirconIntegration/reg_slice/verilog \
    inputs/rtl/aham3soc_armip/logical/nic400_ZirconIntegration/ib_M_AXI_TLX_DATA_ib/verilog \
    inputs/rtl/aham3soc_armip/logical/nic400_ZirconIntegration/nic400/verilog/Axi \
    inputs/rtl/aham3soc_armip/logical/nic400_ZirconIntegration/nic400/verilog/Axi4PC \
    inputs/rtl/aham3soc_armip/logical/nic400_ZirconIntegration/nic400/verilog/Ahb \
    inputs/rtl/aham3soc_armip/logical/nic400_ZirconIntegration/nic400/verilog/AhbPC \
]
