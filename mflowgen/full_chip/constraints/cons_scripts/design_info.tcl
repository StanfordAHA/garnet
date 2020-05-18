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
# Define Port Names (Butterphy)
# ------------------------------------------------------------------------------

set port_names(btfy_jtag_clk)               "pad_jtag_intf_i_phy_tck"

set port_names(btfy_jtag_tdi)               "pad_jtag_intf_i_phy_tdi"
set port_names(btfy_jtag_tdo)               "pad_jtag_intf_i_phy_tdo"
set port_names(btfy_jtag_tms)               "pad_jtag_intf_i_phy_tms"
set port_names(btfy_jtag_reset_n)           "pad_jtag_intf_i_phy_trst_n"
set port_names(btfy_ext_rstb)               "pad_ext_rstb"
set port_names(btfy_ext_dump_start)         "pad_ext_dump_start"

# ------------------------------------------------------------------------------
# Define Port Names (TLX Forward Channel)
# ------------------------------------------------------------------------------

set port_names(tlx_fwd_clk)                 "pad_TLX_FWD_CLK"

set port_names(tlx_fwd_payload_valid)       "pad_TLX_FWD_PAYLOAD_TVALID"
set port_names(tlx_fwd_payload_ready)       "pad_TLX_FWD_PAYLOAD_TREADY"
set port_names(tlx_fwd_payload_data_hi)     "pad_TLX_FWD_PAYLOAD_TDATA_HI"
set port_names(tlx_fwd_payload_data_lo)     "pad_TLX_FWD_PAYLOAD_TDATA_LO"

set port_names(tlx_fwd_flow_valid)          "pad_TLX_FWD_FLOW_TVALID"
set port_names(tlx_fwd_flow_ready)          "pad_TLX_FWD_FLOW_TREADY"
set port_names(tlx_fwd_flow_data)           "pad_TLX_FWD_FLOW_TDATA"

# ------------------------------------------------------------------------------
# Define Port Names (TLX Reverse Channel)
# ------------------------------------------------------------------------------

set port_names(tlx_rev_clk)                 "pad_TLX_REV_CLK"

set port_names(tlx_rev_payload_valid)       "pad_TLX_REV_PAYLOAD_TVALID"
set port_names(tlx_rev_payload_ready)       "pad_TLX_REV_PAYLOAD_TREADY"
set port_names(tlx_rev_payload_data_hi)     "pad_TLX_REV_PAYLOAD_TDATA_HI"
set port_names(tlx_rev_payload_data_lo)     "pad_TLX_REV_PAYLOAD_TDATA_LO"

set port_names(tlx_rev_flow_valid)          "pad_TLX_REV_FLOW_TVALID"
set port_names(tlx_rev_flow_ready)          "pad_TLX_REV_FLOW_TREADY"
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

set port_names(trace_data)                  "pad_TPIU_TRACE_DATA"
set port_names(trace_swo)                   "pad_TPIU_TRACE_SWO"
set port_names(trace_clk)                   "pad_TPIU_TRACE_CLK"

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
# Master Clock and Power-on Reset
# ------------------------------------------------------------------------------

set port_names(master_clk)                  "pad_MASTER_CLK"
set port_names(poreset_n)                   "pad_PORESETn"
