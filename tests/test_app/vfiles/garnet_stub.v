module Garnet (
    input [12:0] axi4_slave_araddr,
    output axi4_slave_arready,
    input axi4_slave_arvalid,
    input [12:0] axi4_slave_awaddr,
    output axi4_slave_awready,
    input axi4_slave_awvalid,
    input axi4_slave_bready,
    output [1:0] axi4_slave_bresp,
    output axi4_slave_bvalid,
    output [31:0] axi4_slave_rdata,
    input axi4_slave_rready,
    output [1:0] axi4_slave_rresp,
    output axi4_slave_rvalid,
    input [31:0] axi4_slave_wdata,
    output axi4_slave_wready,
    input axi4_slave_wvalid,
    output cgra_running_clk_out,
    input clk_in,
    output interrupt,
    input jtag_tck,
    input jtag_tdi,
    output jtag_tdo,
    input jtag_tms,
    input jtag_trst_n,
    input [18:0] proc_packet_rd_addr,
    output [63:0] proc_packet_rd_data,
    output proc_packet_rd_data_valid,
    input proc_packet_rd_en,
    input [18:0] proc_packet_wr_addr,
    input [63:0] proc_packet_wr_data,
    input proc_packet_wr_en,
    input [7:0] proc_packet_wr_strb,
    input reset_in
);
wire GlobalController_cfg_32_32_axi_13_32_inst0$global_controller_inst0_clk_out;
wire GlobalController_cfg_32_32_axi_13_32_inst0$global_controller_inst0_reset_out;
wire [7:0] GlobalController_cfg_32_32_axi_13_32_inst0$global_controller_inst0_cgra_stall;
wire [3:0] GlobalController_cfg_32_32_axi_13_32_inst0$global_controller_inst0_glb_clk_en_master;
wire [3:0] GlobalController_cfg_32_32_axi_13_32_inst0$global_controller_inst0_glb_clk_en_bank_master;
wire [3:0] GlobalController_cfg_32_32_axi_13_32_inst0$global_controller_inst0_glb_pcfg_broadcast_stall;
wire [3:0] GlobalController_cfg_32_32_axi_13_32_inst0$global_controller_inst0_glb_flush_crossbar_sel;
wire GlobalController_cfg_32_32_axi_13_32_inst0$global_controller_inst0_glb_cfg_wr_en;
wire GlobalController_cfg_32_32_axi_13_32_inst0$global_controller_inst0_glb_cfg_wr_clk_en;
wire [11:0] GlobalController_cfg_32_32_axi_13_32_inst0$global_controller_inst0_glb_cfg_wr_addr;
wire [31:0] GlobalController_cfg_32_32_axi_13_32_inst0$global_controller_inst0_glb_cfg_wr_data;
wire GlobalController_cfg_32_32_axi_13_32_inst0$global_controller_inst0_glb_cfg_rd_en;
wire GlobalController_cfg_32_32_axi_13_32_inst0$global_controller_inst0_glb_cfg_rd_clk_en;
wire [11:0] GlobalController_cfg_32_32_axi_13_32_inst0$global_controller_inst0_glb_cfg_rd_addr;
wire GlobalController_cfg_32_32_axi_13_32_inst0$global_controller_inst0_sram_cfg_wr_en;
wire [18:0] GlobalController_cfg_32_32_axi_13_32_inst0$global_controller_inst0_sram_cfg_wr_addr;
wire [31:0] GlobalController_cfg_32_32_axi_13_32_inst0$global_controller_inst0_sram_cfg_wr_data;
wire GlobalController_cfg_32_32_axi_13_32_inst0$global_controller_inst0_sram_cfg_rd_en;
wire [18:0] GlobalController_cfg_32_32_axi_13_32_inst0$global_controller_inst0_sram_cfg_rd_addr;
wire [3:0] GlobalController_cfg_32_32_axi_13_32_inst0$global_controller_inst0_strm_g2f_start_pulse;
wire [3:0] GlobalController_cfg_32_32_axi_13_32_inst0$global_controller_inst0_strm_f2g_start_pulse;
wire [3:0] GlobalController_cfg_32_32_axi_13_32_inst0$global_controller_inst0_pc_start_pulse;
wire GlobalController_cfg_32_32_axi_13_32_inst0$global_controller_inst0_cgra_cfg_read;
wire GlobalController_cfg_32_32_axi_13_32_inst0$global_controller_inst0_cgra_cfg_write;
wire [31:0] GlobalController_cfg_32_32_axi_13_32_inst0$global_controller_inst0_cgra_cfg_addr;
wire [31:0] GlobalController_cfg_32_32_axi_13_32_inst0$global_controller_inst0_cgra_cfg_wr_data;
wire GlobalController_cfg_32_32_axi_13_32_inst0$global_controller_inst0_axi_awready;
wire GlobalController_cfg_32_32_axi_13_32_inst0$global_controller_inst0_axi_wready;
wire [1:0] GlobalController_cfg_32_32_axi_13_32_inst0$global_controller_inst0_axi_bresp;
wire GlobalController_cfg_32_32_axi_13_32_inst0$global_controller_inst0_axi_bvalid;
wire GlobalController_cfg_32_32_axi_13_32_inst0$global_controller_inst0_axi_arready;
wire [31:0] GlobalController_cfg_32_32_axi_13_32_inst0$global_controller_inst0_axi_rdata;
wire [1:0] GlobalController_cfg_32_32_axi_13_32_inst0$global_controller_inst0_axi_rresp;
wire GlobalController_cfg_32_32_axi_13_32_inst0$global_controller_inst0_axi_rvalid;
wire GlobalController_cfg_32_32_axi_13_32_inst0$global_controller_inst0_interrupt;
wire GlobalController_cfg_32_32_axi_13_32_inst0$global_controller_inst0_tdo;
wire [15:0] Interconnect_inst0_io2glb_16_X00_Y00;
wire [15:0] Interconnect_inst0_io2glb_16_X01_Y00;
wire [15:0] Interconnect_inst0_io2glb_16_X02_Y00;
wire [15:0] Interconnect_inst0_io2glb_16_X03_Y00;
wire [15:0] Interconnect_inst0_io2glb_16_X04_Y00;
wire [15:0] Interconnect_inst0_io2glb_16_X05_Y00;
wire [15:0] Interconnect_inst0_io2glb_16_X06_Y00;
wire [15:0] Interconnect_inst0_io2glb_16_X07_Y00;
wire [0:0] Interconnect_inst0_io2glb_1_X00_Y00;
wire [0:0] Interconnect_inst0_io2glb_1_X01_Y00;
wire [0:0] Interconnect_inst0_io2glb_1_X02_Y00;
wire [0:0] Interconnect_inst0_io2glb_1_X03_Y00;
wire [0:0] Interconnect_inst0_io2glb_1_X04_Y00;
wire [0:0] Interconnect_inst0_io2glb_1_X05_Y00;
wire [0:0] Interconnect_inst0_io2glb_1_X06_Y00;
wire [0:0] Interconnect_inst0_io2glb_1_X07_Y00;
wire [31:0] Interconnect_inst0_read_config_data;
wire [0:0] const_0_1_out;
wire [15:0] global_buffer_W_inst0_strm_data_g2f_3_1;
wire [0:0] global_buffer_W_inst0_cgra_cfg_g2f_cfg_rd_en_1_1;
wire [31:0] global_buffer_W_inst0_cgra_cfg_g2f_cfg_data_3_0;
wire [0:0] global_buffer_W_inst0_strm_data_g2f_vld_0_0;
wire [0:0] global_buffer_W_inst0_strm_ctrl_g2f_3_1;
wire [0:0] global_buffer_W_inst0_if_sram_cfg_rd_data_valid;
wire [0:0] global_buffer_W_inst0_strm_ctrl_g2f_0_1;
wire [0:0] global_buffer_W_inst0_strm_data_f2g_rdy_2_1;
wire [31:0] global_buffer_W_inst0_cgra_cfg_g2f_cfg_addr_1_1;
wire [0:0] global_buffer_W_inst0_strm_ctrl_g2f_1_0;
wire [31:0] global_buffer_W_inst0_cgra_cfg_g2f_cfg_addr_0_0;
wire [0:0] global_buffer_W_inst0_cgra_cfg_g2f_cfg_wr_en_0_0;
wire [31:0] global_buffer_W_inst0_cgra_cfg_g2f_cfg_addr_2_1;
wire [31:0] global_buffer_W_inst0_cgra_cfg_g2f_cfg_addr_3_0;
wire [0:0] global_buffer_W_inst0_strm_ctrl_g2f_2_1;
wire [0:0] global_buffer_W_inst0_strm_data_g2f_vld_3_0;
wire [31:0] global_buffer_W_inst0_cgra_cfg_g2f_cfg_addr_0_1;
wire [0:0] global_buffer_W_inst0_cgra_cfg_g2f_cfg_wr_en_0_1;
wire [3:0] global_buffer_W_inst0_pcfg_g2f_interrupt_pulse;
wire [31:0] global_buffer_W_inst0_cgra_cfg_g2f_cfg_addr_3_1;
wire [0:0] global_buffer_W_inst0_cgra_cfg_g2f_cfg_rd_en_0_1;
wire [0:0] global_buffer_W_inst0_cgra_cfg_g2f_cfg_rd_en_0_0;
wire [0:0] global_buffer_W_inst0_cgra_cfg_g2f_cfg_rd_en_2_1;
wire [15:0] global_buffer_W_inst0_strm_data_g2f_0_1;
wire [0:0] global_buffer_W_inst0_strm_ctrl_g2f_1_1;
wire [15:0] global_buffer_W_inst0_strm_data_g2f_2_0;
wire [31:0] global_buffer_W_inst0_if_cfg_rd_data;
wire [0:0] global_buffer_W_inst0_strm_data_f2g_rdy_0_0;
wire [0:0] global_buffer_W_inst0_strm_data_g2f_vld_3_1;
wire [0:0] global_buffer_W_inst0_strm_data_f2g_rdy_3_1;
wire [31:0] global_buffer_W_inst0_if_sram_cfg_rd_data;
wire [0:0] global_buffer_W_inst0_strm_data_flush_g2f_0;
wire [7:0] global_buffer_W_inst0_cgra_stall;
wire [0:0] global_buffer_W_inst0_strm_data_f2g_rdy_1_0;
wire [0:0] global_buffer_W_inst0_cgra_cfg_g2f_cfg_wr_en_3_1;
wire [0:0] global_buffer_W_inst0_cgra_cfg_g2f_cfg_rd_en_1_0;
wire [0:0] global_buffer_W_inst0_cgra_cfg_g2f_cfg_wr_en_2_0;
wire [0:0] global_buffer_W_inst0_strm_data_g2f_vld_1_1;
wire [63:0] global_buffer_W_inst0_proc_rd_data;
wire [0:0] global_buffer_W_inst0_strm_data_f2g_rdy_3_0;
wire [31:0] global_buffer_W_inst0_cgra_cfg_g2f_cfg_data_0_1;
wire [0:0] global_buffer_W_inst0_proc_rd_data_valid;
wire [0:0] global_buffer_W_inst0_strm_data_g2f_vld_2_1;
wire [31:0] global_buffer_W_inst0_cgra_cfg_g2f_cfg_addr_1_0;
wire [0:0] global_buffer_W_inst0_strm_ctrl_g2f_0_0;
wire [15:0] global_buffer_W_inst0_strm_data_g2f_1_0;
wire [0:0] global_buffer_W_inst0_cgra_cfg_g2f_cfg_rd_en_3_0;
wire [0:0] global_buffer_W_inst0_strm_data_flush_g2f_1;
wire [0:0] global_buffer_W_inst0_strm_data_f2g_rdy_0_1;
wire [0:0] global_buffer_W_inst0_cgra_cfg_g2f_cfg_wr_en_1_0;
wire [15:0] global_buffer_W_inst0_strm_data_g2f_3_0;
wire [0:0] global_buffer_W_inst0_cgra_cfg_g2f_cfg_rd_en_3_1;
wire [0:0] global_buffer_W_inst0_cgra_cfg_g2f_cfg_rd_en_2_0;
wire [31:0] global_buffer_W_inst0_cgra_cfg_g2f_cfg_data_3_1;
wire [3:0] global_buffer_W_inst0_strm_f2g_interrupt_pulse;
wire [0:0] global_buffer_W_inst0_if_cfg_rd_data_valid;
wire [15:0] global_buffer_W_inst0_strm_data_g2f_2_1;
wire [0:0] global_buffer_W_inst0_strm_ctrl_g2f_2_0;
wire [0:0] global_buffer_W_inst0_strm_data_g2f_vld_1_0;
wire [0:0] global_buffer_W_inst0_cgra_cfg_g2f_cfg_wr_en_1_1;
wire [15:0] global_buffer_W_inst0_strm_data_g2f_0_0;
wire [31:0] global_buffer_W_inst0_cgra_cfg_g2f_cfg_data_2_0;
wire [0:0] global_buffer_W_inst0_strm_ctrl_g2f_3_0;
wire [31:0] global_buffer_W_inst0_cgra_cfg_g2f_cfg_data_1_1;
wire [0:0] global_buffer_W_inst0_strm_data_f2g_rdy_2_0;
wire [31:0] global_buffer_W_inst0_cgra_cfg_g2f_cfg_data_0_0;
wire [0:0] global_buffer_W_inst0_strm_data_g2f_vld_0_1;
wire [31:0] global_buffer_W_inst0_cgra_cfg_g2f_cfg_addr_2_0;
wire [3:0] global_buffer_W_inst0_strm_g2f_interrupt_pulse;
wire [0:0] global_buffer_W_inst0_strm_data_g2f_vld_2_0;
wire [31:0] global_buffer_W_inst0_cgra_cfg_g2f_cfg_data_2_1;
wire [0:0] global_buffer_W_inst0_cgra_cfg_g2f_cfg_wr_en_3_0;
wire [15:0] global_buffer_W_inst0_strm_data_g2f_1_1;
wire [0:0] global_buffer_W_inst0_cgra_cfg_g2f_cfg_wr_en_2_1;
wire [0:0] global_buffer_W_inst0_strm_data_f2g_rdy_1_1;
wire [31:0] global_buffer_W_inst0_cgra_cfg_g2f_cfg_data_1_0;
global_controller GlobalController_cfg_32_32_axi_13_32_inst0$global_controller_inst0 (
    .clk_in(clk_in),
    .reset_in(reset_in),
    .clk_out(GlobalController_cfg_32_32_axi_13_32_inst0$global_controller_inst0_clk_out),
    .reset_out(GlobalController_cfg_32_32_axi_13_32_inst0$global_controller_inst0_reset_out),
    .cgra_stall(GlobalController_cfg_32_32_axi_13_32_inst0$global_controller_inst0_cgra_stall),
    .glb_clk_en_master(GlobalController_cfg_32_32_axi_13_32_inst0$global_controller_inst0_glb_clk_en_master),
    .glb_clk_en_bank_master(GlobalController_cfg_32_32_axi_13_32_inst0$global_controller_inst0_glb_clk_en_bank_master),
    .glb_pcfg_broadcast_stall(GlobalController_cfg_32_32_axi_13_32_inst0$global_controller_inst0_glb_pcfg_broadcast_stall),
    .glb_flush_crossbar_sel(GlobalController_cfg_32_32_axi_13_32_inst0$global_controller_inst0_glb_flush_crossbar_sel),
    .glb_cfg_wr_en(GlobalController_cfg_32_32_axi_13_32_inst0$global_controller_inst0_glb_cfg_wr_en),
    .glb_cfg_wr_clk_en(GlobalController_cfg_32_32_axi_13_32_inst0$global_controller_inst0_glb_cfg_wr_clk_en),
    .glb_cfg_wr_addr(GlobalController_cfg_32_32_axi_13_32_inst0$global_controller_inst0_glb_cfg_wr_addr),
    .glb_cfg_wr_data(GlobalController_cfg_32_32_axi_13_32_inst0$global_controller_inst0_glb_cfg_wr_data),
    .glb_cfg_rd_en(GlobalController_cfg_32_32_axi_13_32_inst0$global_controller_inst0_glb_cfg_rd_en),
    .glb_cfg_rd_clk_en(GlobalController_cfg_32_32_axi_13_32_inst0$global_controller_inst0_glb_cfg_rd_clk_en),
    .glb_cfg_rd_addr(GlobalController_cfg_32_32_axi_13_32_inst0$global_controller_inst0_glb_cfg_rd_addr),
    .glb_cfg_rd_data(global_buffer_W_inst0_if_cfg_rd_data),
    .glb_cfg_rd_data_valid(global_buffer_W_inst0_if_cfg_rd_data_valid[0]),
    .sram_cfg_wr_en(GlobalController_cfg_32_32_axi_13_32_inst0$global_controller_inst0_sram_cfg_wr_en),
    .sram_cfg_wr_addr(GlobalController_cfg_32_32_axi_13_32_inst0$global_controller_inst0_sram_cfg_wr_addr),
    .sram_cfg_wr_data(GlobalController_cfg_32_32_axi_13_32_inst0$global_controller_inst0_sram_cfg_wr_data),
    .sram_cfg_rd_en(GlobalController_cfg_32_32_axi_13_32_inst0$global_controller_inst0_sram_cfg_rd_en),
    .sram_cfg_rd_addr(GlobalController_cfg_32_32_axi_13_32_inst0$global_controller_inst0_sram_cfg_rd_addr),
    .sram_cfg_rd_data(global_buffer_W_inst0_if_sram_cfg_rd_data),
    .sram_cfg_rd_data_valid(global_buffer_W_inst0_if_sram_cfg_rd_data_valid[0]),
    .strm_g2f_start_pulse(GlobalController_cfg_32_32_axi_13_32_inst0$global_controller_inst0_strm_g2f_start_pulse),
    .strm_f2g_start_pulse(GlobalController_cfg_32_32_axi_13_32_inst0$global_controller_inst0_strm_f2g_start_pulse),
    .pc_start_pulse(GlobalController_cfg_32_32_axi_13_32_inst0$global_controller_inst0_pc_start_pulse),
    .strm_g2f_interrupt_pulse(global_buffer_W_inst0_strm_g2f_interrupt_pulse),
    .strm_f2g_interrupt_pulse(global_buffer_W_inst0_strm_f2g_interrupt_pulse),
    .pcfg_g2f_interrupt_pulse(global_buffer_W_inst0_pcfg_g2f_interrupt_pulse),
    .cgra_cfg_read(GlobalController_cfg_32_32_axi_13_32_inst0$global_controller_inst0_cgra_cfg_read),
    .cgra_cfg_write(GlobalController_cfg_32_32_axi_13_32_inst0$global_controller_inst0_cgra_cfg_write),
    .cgra_cfg_addr(GlobalController_cfg_32_32_axi_13_32_inst0$global_controller_inst0_cgra_cfg_addr),
    .cgra_cfg_wr_data(GlobalController_cfg_32_32_axi_13_32_inst0$global_controller_inst0_cgra_cfg_wr_data),
    .cgra_cfg_rd_data(Interconnect_inst0_read_config_data),
    .axi_awaddr(axi4_slave_awaddr),
    .axi_awvalid(axi4_slave_awvalid),
    .axi_awready(GlobalController_cfg_32_32_axi_13_32_inst0$global_controller_inst0_axi_awready),
    .axi_wdata(axi4_slave_wdata),
    .axi_wvalid(axi4_slave_wvalid),
    .axi_wready(GlobalController_cfg_32_32_axi_13_32_inst0$global_controller_inst0_axi_wready),
    .axi_bready(axi4_slave_bready),
    .axi_bresp(GlobalController_cfg_32_32_axi_13_32_inst0$global_controller_inst0_axi_bresp),
    .axi_bvalid(GlobalController_cfg_32_32_axi_13_32_inst0$global_controller_inst0_axi_bvalid),
    .axi_araddr(axi4_slave_araddr),
    .axi_arvalid(axi4_slave_arvalid),
    .axi_arready(GlobalController_cfg_32_32_axi_13_32_inst0$global_controller_inst0_axi_arready),
    .axi_rdata(GlobalController_cfg_32_32_axi_13_32_inst0$global_controller_inst0_axi_rdata),
    .axi_rresp(GlobalController_cfg_32_32_axi_13_32_inst0$global_controller_inst0_axi_rresp),
    .axi_rvalid(GlobalController_cfg_32_32_axi_13_32_inst0$global_controller_inst0_axi_rvalid),
    .axi_rready(axi4_slave_rready),
    .interrupt(GlobalController_cfg_32_32_axi_13_32_inst0$global_controller_inst0_interrupt),
    .tck(jtag_tck),
    .tdi(jtag_tdi),
    .tms(jtag_tms),
    .trst_n(jtag_trst_n),
    .tdo(GlobalController_cfg_32_32_axi_13_32_inst0$global_controller_inst0_tdo)
);
assign axi4_slave_arready = GlobalController_cfg_32_32_axi_13_32_inst0$global_controller_inst0_axi_arready;
assign axi4_slave_awready = GlobalController_cfg_32_32_axi_13_32_inst0$global_controller_inst0_axi_awready;
assign axi4_slave_bresp = GlobalController_cfg_32_32_axi_13_32_inst0$global_controller_inst0_axi_bresp;
assign axi4_slave_bvalid = GlobalController_cfg_32_32_axi_13_32_inst0$global_controller_inst0_axi_bvalid;
// assign axi4_slave_rdata = GlobalController_cfg_32_32_axi_13_32_inst0$global_controller_inst0_axi_rdata;
assign axi4_slave_rresp = GlobalController_cfg_32_32_axi_13_32_inst0$global_controller_inst0_axi_rresp;
assign axi4_slave_rvalid = GlobalController_cfg_32_32_axi_13_32_inst0$global_controller_inst0_axi_rvalid;
assign axi4_slave_wready = GlobalController_cfg_32_32_axi_13_32_inst0$global_controller_inst0_axi_wready;
assign cgra_running_clk_out = GlobalController_cfg_32_32_axi_13_32_inst0$global_controller_inst0_clk_out;
// assign interrupt = GlobalController_cfg_32_32_axi_13_32_inst0$global_controller_inst0_interrupt;
assign jtag_tdo = GlobalController_cfg_32_32_axi_13_32_inst0$global_controller_inst0_tdo;

// # write to pcfg (0x1c): count to 15, then raise interrupt
// # (clear) write to PAR_CFG:     clear interrupt
// # 
// # write to strm (0x18): count to 15, then raise interrupt
// # (clear) write to STRM_G2F (0x34): DON'T clear interrupt, b/c F2G is comin lawd
// # (clear) write to STRM_F2G (0x30): clear interrupt, b/c now done w F2G *and* G2F



    // While garnet is stubbed out, this emulates cgra and stream config.
    // Also see tb/Environment.sv stall/unstall commands.
    // A write of 0x1 to a config addr starts the "configuration".
    // We pretend like it takes 20cy to complete the config,
    // then we flag an interrupt to say "done".
    logic [7:0] stub_cnt;
    logic stub_interrupt;
    always_ff @(posedge clk_in, posedge reset_in) begin
        if (reset_in) begin
            stub_cnt <= 8'h0;
        end else if (
            (axi4_slave_wdata == 32'h1)
            & (  (axi4_slave_awaddr == 12'h1c)  // cgra config stall "pcfg"
               | (axi4_slave_awaddr == 12'h18)  // strm config stall "strm"
              )
            & (axi4_slave_wvalid == 1'b1)
        ) begin
            stub_cnt <= 8'hf;  // Wait this many cycles before setting interrupt to say done
        end else if (stub_cnt > 8'h0) begin
            stub_cnt <= stub_cnt - 8'h1;
        end
    end

    // Copied from glc.svh
    `define GLC_PAR_CFG_G2F_ISR_R 'h38
    `define GLC_STRM_G2F_ISR_R    'h34
    `define GLC_STRM_F2G_ISR_R    'h30
    `define GLC_GLOBAL_ISR_R      'h3c

    // stub_cnt timeout sets the interrupt;
    // a write to any ISR clears the interrupt
    // TODO there should be a separate interrupt reg for each ISR maybe
    // Also see tb/Environment.sv wait_interrupt(), clear_interrupt()
    always_ff @(posedge clk_in, posedge reset_in) begin
        if (reset_in) begin
            stub_interrupt <= 1'b0;
        end else if (
            (axi4_slave_wdata == 32'h1)
            & ((axi4_slave_awaddr == `GLC_PAR_CFG_G2F_ISR_R)  // 0x38
              // |(axi4_slave_awaddr == `GLC_STRM_G2F_ISR_R)     // 0x34  see above
              |(axi4_slave_awaddr == `GLC_STRM_F2G_ISR_R)     // 0x30
              |(axi4_slave_awaddr == `GLC_GLOBAL_ISR_R))
            & (axi4_slave_wvalid == 1'b1)
        ) begin
            stub_interrupt <= 1'b0;

        end else if (stub_cnt == 8'h1) begin
            stub_interrupt <= 1'b1;
        // end else if (stub_cnt == 8'h1) begin
        //    stub_interrupt <= 1'b0;
        end
    end
    assign interrupt = stub_interrupt;

    // If testbench asks for data from an ISR, we send out the
    // response 0xffff... to fool it into thinking everthing's done haha
    logic [31:0] foolers_data;
    always_ff @(posedge clk_in) begin
        if ((axi4_slave_araddr == `GLC_PAR_CFG_G2F_ISR_R)
           |(axi4_slave_araddr == `GLC_STRM_G2F_ISR_R)
           |(axi4_slave_araddr == `GLC_STRM_F2G_ISR_R)
           |(axi4_slave_araddr == `GLC_GLOBAL_ISR_R))
          begin
              foolers_data <= 32'hffffffff;
          end
    end
    assign axi4_slave_rdata = foolers_data;

//   always @(posedge clk_in) begin
//      $display("garnet.v 227 i see axi4_slave_wvalid = %d", axi4_slave_wvalid); $fflush();
//   end

    // What if...?
    logic [63:0] proc_packet_rd_data_reg;
    logic [ 0:0] proc_packet_rd_data_valid_reg;
    always_ff @(posedge clk_in) begin
        if (proc_packet_rd_en == 1'b1) begin
            proc_packet_rd_data_reg <= proc_packet_rd_addr + 1'b1;  // Is this too weird?
            proc_packet_rd_data_valid_reg <= 1'b1;
        end else begin
          proc_packet_rd_data_valid_reg <= 1'b0;
        end
    end
    assign proc_packet_rd_data       = proc_packet_rd_data_reg;
    assign proc_packet_rd_data_valid = proc_packet_rd_data_valid_reg;

    // Timescale test. Look at waveforms to see if they shifted correctly.
    // Clocks have 1ns cycle time.
    // LHS/RHS edges should be shifted 100ps to left of OG clock.
    // Note LHS and RHS look exactly the same

    logic clk_dly_rhs;
    always_ff @(posedge clk_in or negedge clk_in) begin
        clk_dly_rhs <= #100 clk_in;
    end
    logic clk_dly_lhs;
    always_ff @(posedge clk_in or negedge clk_in) begin
        #100 clk_dly_lhs <= clk_in;
    end

endmodule

//    output [31:0] axi4_slave_rdata,
