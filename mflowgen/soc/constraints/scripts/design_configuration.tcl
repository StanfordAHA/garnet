#-----------------------------------------------------------------------------
# Synopsys Design Constraint (SDC) File
#-----------------------------------------------------------------------------
# Purpose: Design Info Variables
#------------------------------------------------------------------------------
#
#
# Author   : Gedeon Nyengele
# Date     : May 9, 2020
#------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
# Define Port Names
# ------------------------------------------------------------------------------
set port_prefix                         ""

# Resets
set port_names(poreset)                   [string cat ${port_prefix} PORESETn]
set port_names(dp_jtag_reset)             [string cat ${port_prefix} DP_JTAG_TRSTn]
set port_names(cgra_jtag_reset)           [string cat ${port_prefix} CGRA_JTAG_TRSTn]

# input clocks
set port_names(master_clk)                [string cat ${port_prefix} MASTER_CLK]
set port_names(dp_jtag_clk)               [string cat ${port_prefix} DP_JTAG_TCK]
set port_names(cgra_jtag_clk)             [string cat ${port_prefix} CGRA_JTAG_TCK]
set port_names(tlx_rev_clk)               [string cat ${port_prefix} TLX_REV_CLK]

# DP JTAG
set port_names(dp_jtag_tdi)               [string cat ${port_prefix} DP_JTAG_TDI]
set port_names(dp_jtag_tms)               [string cat ${port_prefix} DP_JTAG_TMS]
set port_names(dp_jtag_tdo)               [string cat ${port_prefix} DP_JTAG_TDO]

# CGRA JTAG
set port_names(cgra_jtag_tdi)             [string cat ${port_prefix} CGRA_JTAG_TDI]
set port_names(cgra_jtag_tms)             [string cat ${port_prefix} CGRA_JTAG_TMS]
set port_names(cgra_jtag_tdo)             [string cat ${port_prefix} CGRA_JTAG_TDO]

# TPIU
set port_names(tpiu_trace_data)           [string cat ${port_prefix} TPIU_TRACE_DATA]
set port_names(tpiu_trace_swo)            [string cat ${port_prefix} TPIU_TRACE_SWO]
set port_names(tpiu_trace_clk)            [string cat ${port_prefix} TPIU_TRACE_CLK]

# UART
set port_names(uart0_rxd)                 [string cat ${port_prefix} UART0_RXD]
set port_names(uart0_txd)                 [string cat ${port_prefix} UART0_TXD]
set port_names(uart1_rxd)                 [string cat ${port_prefix} UART1_RXD]
set port_names(uart1_txd)                 [string cat ${port_prefix} UART1_TXD]

# TLX FWD
set port_names(tlx_fwd_clk)               [string cat ${port_prefix} TLX_FWD_CLK]

set port_names(tlx_fwd_payload_tvalid)    [string cat ${port_prefix} TLX_FWD_PAYLOAD_TVALID]
set port_names(tlx_fwd_payload_tready)    [string cat ${port_prefix} TLX_FWD_PAYLOAD_TREADY]
set port_names(tlx_fwd_payload_tdata_lo)  [string cat ${port_prefix} TLX_FWD_PAYLOAD_TDATA_LO]
set port_names(tlx_fwd_payload_tdata_hi)  [string cat ${port_prefix} TLX_FWD_PAYLOAD_TDATA_HI]

set port_names(tlx_fwd_flow_tvalid)       [string cat ${port_prefix} TLX_FWD_FLOW_TVALID]
set port_names(tlx_fwd_flow_tready)       [string cat ${port_prefix} TLX_FWD_FLOW_TREADY]
set port_names(tlx_fwd_flow_tdata)        [string cat ${port_prefix} TLX_FWD_FLOW_TDATA]

# TLX REV
set port_names(tlx_rev_payload_tvalid)     [string cat ${port_prefix} TLX_REV_PAYLOAD_TVALID]
set port_names(tlx_rev_payload_tready)     [string cat ${port_prefix} TLX_REV_PAYLOAD_TREADY]
set port_names(tlx_rev_payload_tdata_lo)   [string cat ${port_prefix} TLX_REV_PAYLOAD_TDATA_LO]
set port_names(tlx_rev_payload_tdata_hi)   [string cat ${port_prefix} TLX_REV_PAYLOAD_TDATA_HI]

set port_names(tlx_rev_flow_tvalid)       [string cat ${port_prefix} TLX_REV_FLOW_TVALID]
set port_names(tlx_rev_flow_tready)       [string cat ${port_prefix} TLX_REV_FLOW_TREADY]
set port_names(tlx_rev_flow_tdata)        [string cat ${port_prefix} TLX_REV_FLOW_TDATA]

# Pad Strengh Control
set port_names(out_pad_ds_grp0)           [string cat ${port_prefix} OUT_PAD_DS_GRP0]
set port_names(out_pad_ds_grp1)           [string cat ${port_prefix} OUT_PAD_DS_GRP1]
set port_names(out_pad_ds_grp2)           [string cat ${port_prefix} OUT_PAD_DS_GRP2]
set port_names(out_pad_ds_grp3)           [string cat ${port_prefix} OUT_PAD_DS_GRP3]
set port_names(out_pad_ds_grp4)           [string cat ${port_prefix} OUT_PAD_DS_GRP4]
set port_names(out_pad_ds_grp5)           [string cat ${port_prefix} OUT_PAD_DS_GRP5]
set port_names(out_pad_ds_grp6)           [string cat ${port_prefix} OUT_PAD_DS_GRP6]
set port_names(out_pad_ds_grp7)           [string cat ${port_prefix} OUT_PAD_DS_GRP7]

# Loop Back
set port_names(loop_back_select)          [string cat ${port_prefix} LOOP_BACK_SELECT]
set port_names(loop_back)                 [string cat ${port_prefix} LOOP_BACK]

# ------------------------------------------------------------------------------
# Clock and Reset Port Names
# ------------------------------------------------------------------------------

set clock_ports   [list   $port_names(master_clk) \
                          $port_names(dp_jtag_clk) \
                          $port_names(cgra_jtag_clk) \
                          $port_names(tlx_rev_clk) \
                  ]

set reset_ports   [list   $port_names(poreset) \
                          $port_names(dp_jtag_reset) \
                          $port_names(cgra_jtag_reset) \
                  ]

# ------------------------------------------------------------------------------
# Hierarchy path to Top
# ------------------------------------------------------------------------------

set top_path      ""
