# ==============================================================================
# Include Paths for NIC400 IP
# ==============================================================================
set soc_inc_nic400 [concat \
  inputs/rtl/components/nic450/logical/nic400_nic/amib_apb_group_peripherals/verilog \
  inputs/rtl/components/nic450/logical/nic400_nic/amib_master_CGRA_DATA/verilog \
  inputs/rtl/components/nic450/logical/nic400_nic/amib_master_CGRA_REG/verilog \
  inputs/rtl/components/nic450/logical/nic400_nic/amib_master_SRAM0/verilog \
  inputs/rtl/components/nic450/logical/nic400_nic/amib_master_SRAM1/verilog \
  inputs/rtl/components/nic450/logical/nic400_nic/amib_master_SRAM2/verilog \
  inputs/rtl/components/nic450/logical/nic400_nic/amib_master_SRAM3/verilog \
  inputs/rtl/components/nic450/logical/nic400_nic/amib_master_SRAM4/verilog \
  inputs/rtl/components/nic450/logical/nic400_nic/amib_master_SRAM5/verilog \
  inputs/rtl/components/nic450/logical/nic400_nic/amib_master_TLX/verilog \
  inputs/rtl/components/nic450/logical/nic400_nic/asib_slave_DMA0/verilog \
  inputs/rtl/components/nic450/logical/nic400_nic/asib_slave_DMA1/verilog \
  inputs/rtl/components/nic450/logical/nic400_nic/asib_slave_M3_DI/verilog \
  inputs/rtl/components/nic450/logical/nic400_nic/asib_slave_M3_SYS/verilog \
  inputs/rtl/components/nic450/logical/nic400_nic/busmatrix_bm0/verilog \
  inputs/rtl/components/nic450/logical/nic400_nic/busmatrix_bm1/verilog \
  inputs/rtl/components/nic450/logical/nic400_nic/cdc_blocks/verilog \
  inputs/rtl/components/nic450/logical/nic400_nic/default_slave_ds_2/verilog \
  inputs/rtl/components/nic450/logical/nic400_nic/ib_apb_group_peripherals_ib/verilog \
  inputs/rtl/components/nic450/logical/nic400_nic/ib_master_CGRA_DATA_ib/verilog \
  inputs/rtl/components/nic450/logical/nic400_nic/ib_master_CGRA_REG_ib/verilog \
  inputs/rtl/components/nic450/logical/nic400_nic/ib_master_TLX_ib/verilog \
  inputs/rtl/components/nic450/logical/nic400_nic/ib_slave_M3_DI_ib/verilog \
  inputs/rtl/components/nic450/logical/nic400_nic/ib_slave_M3_SYS_ib/verilog \
  inputs/rtl/components/nic450/logical/nic400_nic/reg_slice/verilog \
  inputs/rtl/components/nic450/logical/nic400_nic/nic400/verilog/Axi \
  inputs/rtl/components/nic450/logical/nic400_nic/nic400/verilog/Ahb \
]
