#-----------------------------------------------------------------------------
# TCL Script
#-----------------------------------------------------------------------------
# Purpose: Design Info
#------------------------------------------------------------------------------
#
# Author   : Gedeon Nyengele
# Date     : May 14, 2020
#------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
# Define Port Names (XGCD)
# ------------------------------------------------------------------------------

set port_names(xgcd_ext_clk)                "pad_XGCD_EXT_CLK"
set port_names(xgcd_clk_select)             "pad_XGCD_CLK_SELECT"
set port_names(xgcd_div8_clk)               "pad_XGCD_DIV8_CLK"
set port_names(xgcd0_start)                 "pad_XGCD0_START"
set port_names(xgcd1_start)                 "pad_XGCD1_START"
set port_names(xgcd0_done)                  "pad_XGCD0_DONE"
set port_names(xgcd1_done)                  "pad_XGCD1_DONE"

# ------------------------------------------------------------------------------
# Define Port Names (TLX Forward Channel)
# ------------------------------------------------------------------------------

set port_names(tlx_fwd_clk)                 "pad_TLX_FWD_CLK"

set port_names(tlx_fwd_payload_valid)       "pad_TLX_FWD_PAYLOAD_TVALID"
set port_names(tlx_fwd_payload_data_hi)     "pad_TLX_FWD_PAYLOAD_TDATA_HI"
set port_names(tlx_fwd_payload_data_lo)     "pad_TLX_FWD_PAYLOAD_TDATA_LO"

set port_names(tlx_fwd_flow_valid)          "pad_TLX_FWD_FLOW_TVALID"
set port_names(tlx_fwd_flow_data)           "pad_TLX_FWD_FLOW_TDATA"

# ------------------------------------------------------------------------------
# Define Port Names (TLX Reverse Channel)
# ------------------------------------------------------------------------------

set port_names(tlx_rev_clk)                 "pad_TLX_REV_CLK"

set port_names(tlx_rev_payload_valid)       "pad_TLX_REV_PAYLOAD_TVALID"
set port_names(tlx_rev_payload_data_hi)     "pad_TLX_REV_PAYLOAD_TDATA_HI"
set port_names(tlx_rev_payload_data_lo)     "pad_TLX_REV_PAYLOAD_TDATA_LO"

set port_names(tlx_rev_flow_valid)          "pad_TLX_REV_FLOW_TVALID"
set port_names(tlx_rev_flow_data)           "pad_TLX_REV_FLOW_TDATA"

# ------------------------------------------------------------------------------
# Define Port Names (Debug Port JTAG)
# ------------------------------------------------------------------------------

set port_names(dp_jtag_clk)                 "pad_DP_JTAG_TCK"

set port_names(dp_jtag_tdi)                 "pad_DP_JTAG_TDI"
set port_names(dp_jtag_tdo)                 "pad_DP_JTAG_TDO"
set port_names(dp_jtag_tms)                 "pad_DP_JTAG_TMS"
set port_names(dp_jtag_reset_n)             "pad_DP_JTAG_TRSTn"

# ------------------------------------------------------------------------------
# Define Port Names (CGRA JTAG)
# ------------------------------------------------------------------------------

set port_names(cgra_jtag_clk)               "pad_CGRA_JTAG_TCK"

set port_names(cgra_jtag_tdi)               "pad_CGRA_JTAG_TDI"
set port_names(cgra_jtag_tdo)               "pad_CGRA_JTAG_TDO"
set port_names(cgra_jtag_tms)               "pad_CGRA_JTAG_TMS"
set port_names(cgra_jtag_reset_n)           "pad_CGRA_JTAG_TRSTn"


# ------------------------------------------------------------------------------
# Define Port Names (Trace Port)
# ------------------------------------------------------------------------------

set port_names(trace_swo)                   "pad_TPIU_TRACE_SWO"
set port_names(trace_clkin)                 "pad_TPIU_TRACECLKIN"

# ------------------------------------------------------------------------------
# Define Port Names (UART)
# ------------------------------------------------------------------------------

set port_names(uart0_rxd)                   "pad_UART0_RXD"
set port_names(uart0_txd)                   "pad_UART0_TXD"

set port_names(uart1_rxd)                   "pad_UART1_RXD"
set port_names(uart1_txd)                   "pad_UART1_TXD"

# ------------------------------------------------------------------------------
# Define Port Names (Loop Back)
# ------------------------------------------------------------------------------

set port_names(loop_back)                   "pad_LOOP_BACK"
set port_names(loop_back_select)            "pad_LOOP_BACK_SELECT"

# ------------------------------------------------------------------------------
# Master Clock and Resets
# ------------------------------------------------------------------------------

set port_names(master_clk)                  "pad_MASTER_CLK"
set port_names(poreset_n)                   "pad_PORESETn"
set port_names(sysreset_n)                  "pad_SYSRESETn"
