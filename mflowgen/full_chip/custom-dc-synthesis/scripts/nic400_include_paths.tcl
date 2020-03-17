# ==============================================================================
# Include Paths for NIC400 IP
# ==============================================================================
set soc_inc_nic400 [concat \
  rtl/components/nic450/logical/nic400_nic/amib_apb_group_peripherals/verilog \
  rtl/components/nic450/logical/nic400_nic/amib_master_CGRA_DATA/verilog \
  rtl/components/nic450/logical/nic400_nic/amib_master_CGRA_REG/verilog \
  rtl/components/nic450/logical/nic400_nic/amib_master_SRAM0/verilog \
  rtl/components/nic450/logical/nic400_nic/amib_master_SRAM1/verilog \
  rtl/components/nic450/logical/nic400_nic/amib_master_SRAM2/verilog \
  rtl/components/nic450/logical/nic400_nic/amib_master_SRAM3/verilog \
  rtl/components/nic450/logical/nic400_nic/amib_master_SRAM4/verilog \
  rtl/components/nic450/logical/nic400_nic/amib_master_SRAM5/verilog \
  rtl/components/nic450/logical/nic400_nic/amib_master_TLX/verilog \
  rtl/components/nic450/logical/nic400_nic/asib_slave_DMA0/verilog \
  rtl/components/nic450/logical/nic400_nic/asib_slave_DMA1/verilog \
  rtl/components/nic450/logical/nic400_nic/asib_slave_M3_DI/verilog \
  rtl/components/nic450/logical/nic400_nic/asib_slave_M3_SYS/verilog \
  rtl/components/nic450/logical/nic400_nic/busmatrix_bm0/verilog \
  rtl/components/nic450/logical/nic400_nic/busmatrix_bm1/verilog \
  rtl/components/nic450/logical/nic400_nic/cdc_blocks/verilog \
  rtl/components/nic450/logical/nic400_nic/default_slave_ds_2/verilog \
  rtl/components/nic450/logical/nic400_nic/ib_apb_group_peripherals_ib/verilog \
  rtl/components/nic450/logical/nic400_nic/ib_master_CGRA_DATA_ib/verilog \
  rtl/components/nic450/logical/nic400_nic/ib_master_CGRA_REG_ib/verilog \
  rtl/components/nic450/logical/nic400_nic/ib_master_TLX_ib/verilog \
  rtl/components/nic450/logical/nic400_nic/ib_slave_M3_DI_ib/verilog \
  rtl/components/nic450/logical/nic400_nic/ib_slave_M3_SYS_ib/verilog \
  rtl/components/nic450/logical/nic400_nic/reg_slice/verilog \
  rtl/components/nic450/logical/nic400_nic/nic400/verilog/Axi \
  rtl/components/nic450/logical/nic400_nic/nic400/verilog/Ahb \
]
