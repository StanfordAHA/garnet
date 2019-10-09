/*=============================================================================
** Module: glb_host_interconnect.sv
** Description:
**              Interconnect for processor data in global buffer
** Author: Taeyoung Kong
** Change history: 10/07/2019 - Implement first version
**===========================================================================*/
import global_buffer_pkg::*;

module glb_host_interconnect (
    input  logic                            clk,
    input  logic                            reset,
    input  logic [TILE_SEL_ADDR_WIDTH-1:0]  glb_tile_col,
    
    // East
    input  logic                            h2b_wr_en_esti,
    input  logic [BANK_DATA_WIDTH/8-1:0]    h2b_wr_strb_esti,
    input  logic [GLB_ADDR_WIDTH-1:0]       h2b_wr_addr_esti,
    input  logic [BANK_DATA_WIDTH-1:0]      h2b_wr_data_esti,
    input  logic                            h2b_rd_en_esti,
    input  logic [GLB_ADDR_WIDTH-1:0]       h2b_rd_addr_esti,
    output logic [BANK_DATA_WIDTH-1:0]      b2h_rd_data_esto,

    // West
    output logic                            h2b_wr_en_wsto,
    output logic [BANK_DATA_WIDTH/8-1:0]    h2b_wr_strb_wsto,
    output logic [GLB_ADDR_WIDTH-1:0]       h2b_wr_addr_wsto,
    output logic [BANK_DATA_WIDTH-1:0]      h2b_wr_data_wsto,
    output logic                            h2b_rd_en_wsto,
    output logic [GLB_ADDR_WIDTH-1:0]       h2b_rd_addr_wsto,
    input  logic [BANK_DATA_WIDTH-1:0]      b2h_rd_data_wsti,

    // Bank
    output logic                            h2b_wr_en [0:NUM_BANKS-1],
    output logic [BANK_DATA_WIDTH-1:0]      h2b_wr_data [0:NUM_BANKS-1],
    output logic [BANK_DATA_WIDTH-1:0]      h2b_wr_data_bit_sel [0:NUM_BANKS-1],
    output logic [BANK_ADDR_WIDTH-1:0]      h2b_wr_addr [0:NUM_BANKS-1],
    output logic                            h2b_rd_en [0:NUM_BANKS-1],
    output logic [BANK_ADDR_WIDTH-1:0]      h2b_rd_addr [0:NUM_BANKS-1],
    input  logic [BANK_DATA_WIDTH-1:0]      b2h_rd_data [0:NUM_BANKS-1]
);

//============================================================================//
// internal logic declaration for write
//============================================================================//
logic                           int_tile_h2b_wr_en;
logic [BANK_SEL_ADDR_WIDTH-1:0] int_h2b_wr_bank_sel;
logic                           int_h2b_wr_en [0:NUM_BANKS-1];
logic [BANK_DATA_WIDTH-1:0]     int_h2b_wr_data;
logic [BANK_DATA_WIDTH-1:0]     int_h2b_wr_data_bit_sel;
logic [BANK_ADDR_WIDTH-1:0]     int_h2b_wr_addr;

logic                           int_h2b_wr_en_d1 [0:NUM_BANKS-1];
logic [BANK_DATA_WIDTH-1:0]     int_h2b_wr_data_d1;
logic [BANK_DATA_WIDTH-1:0]     int_h2b_wr_data_bit_sel_d1;
logic [BANK_ADDR_WIDTH-1:0]     int_h2b_wr_addr_d1;

//============================================================================//
// write muxing
//============================================================================//
assign int_tile_h2b_wr_en = h2b_wr_en_esti && (glb_tile_col == h2b_wr_addr_esti[BANK_ADDR_WIDTH + BANK_SEL_ADDR_WIDTH +: TILE_SEL_ADDR_WIDTH]);
assign int_h2b_wr_bank_sel = h2b_wr_addr_esti[BANK_ADDR_WIDTH +: BANK_SEL_ADDR_WIDTH];
always_comb begin
    for (int i=0; i<NUM_BANKS; i=i+1) begin
       int_h2b_wr_en[i] = int_tile_h2b_wr_en && (i == int_h2b_wr_bank_sel);
    end
end
assign int_h2b_wr_data = h2b_wr_data_esti;
assign int_h2b_wr_addr = h2b_wr_addr_esti[0 +: BANK_ADDR_WIDTH];
always_comb begin
    for (int i=0; i<BANK_DATA_WIDTH/8; i=i+1) begin
        // Byte-addressable
        int_h2b_wr_data_bit_sel[i*8 +: 8] = {8{h2b_wr_strb_esti[i]}};
    end
end

//============================================================================//
// write pipelining
//============================================================================//
always_ff @ (posedge clk) begin
    for (int i=0; i<NUM_BANKS; i=i+1) begin
        int_h2b_wr_en_d1[i] <= int_h2b_wr_en[i];
    end
    int_h2b_wr_addr_d1 <= int_h2b_wr_addr;
    int_h2b_wr_data_d1 <= int_h2b_wr_data;
    int_h2b_wr_data_bit_sel_d1 <= int_h2b_wr_data_bit_sel;
end

//============================================================================//
// write output assignment
//============================================================================//
always_comb begin
    for (int i=0; i<NUM_BANKS; i=i+1) begin
        h2b_wr_en[i] = int_h2b_wr_en_d1[i];
        h2b_wr_addr[i] = int_h2b_wr_addr_d1;
        h2b_wr_data[i] = int_h2b_wr_data_d1;
        h2b_wr_data_bit_sel[i] = int_h2b_wr_data_bit_sel_d1;
    end
end

//============================================================================//
// internal logic declaration for read
//============================================================================//
logic                           int_tile_h2b_rd_en;
logic                           int_h2b_rd_en [0:NUM_BANKS-1];
logic [BANK_SEL_ADDR_WIDTH-1:0] int_h2b_rd_bank_sel;
logic [BANK_DATA_WIDTH-1:0]     int_b2h_rd_data;
logic [BANK_ADDR_WIDTH-1:0]     int_h2b_rd_addr;

logic [BANK_DATA_WIDTH-1:0]     int_b2h_rd_data_d1 [0:NUM_BANKS-1];
logic                           int_tile_h2b_rd_en_d1;
logic [BANK_SEL_ADDR_WIDTH-1:0] int_h2b_rd_bank_sel_d1;

logic                           int_tile_h2b_rd_en_d2;
logic [BANK_SEL_ADDR_WIDTH-1:0] int_h2b_rd_bank_sel_d2;

logic                           h2b_rd_en_d1;
logic                           h2b_rd_en_d2;

//============================================================================//
// read muxing
//============================================================================//
assign int_tile_h2b_rd_en = h2b_rd_en_esti && (glb_tile_col == h2b_rd_addr_esti[BANK_ADDR_WIDTH + BANK_SEL_ADDR_WIDTH +: TILE_SEL_ADDR_WIDTH]);
assign int_h2b_rd_bank_sel = h2b_rd_addr_esti[BANK_ADDR_WIDTH +: BANK_SEL_ADDR_WIDTH];
always_comb begin
    for (int i=0; i<NUM_BANKS; i=i+1) begin
        int_h2b_rd_en[i] = int_tile_h2b_rd_en && (i == int_h2b_rd_bank_sel);
    end
end

assign int_h2b_rd_addr = h2b_rd_addr_esti[0 +: BANK_ADDR_WIDTH];

//============================================================================//
// read pipelining
//============================================================================//
always_ff @(posedge clk) begin
    int_h2b_rd_bank_sel_d1 <= int_h2b_rd_bank_sel;
    int_h2b_rd_bank_sel_d2 <= int_h2b_rd_bank_sel_d1;
end

always_ff @(posedge clk) begin
    int_tile_h2b_rd_en_d1 <= int_tile_h2b_rd_en;
    int_tile_h2b_rd_en_d2 <= int_tile_h2b_rd_en_d1;
end

always_ff @(posedge clk) begin
    for (int i=0; i<NUM_BANKS; i=i+1) begin
        int_b2h_rd_data_d1[i] <= b2h_rd_data[i];
    end
end

always_ff @(posedge clk) begin
    h2b_rd_en_d1 <= h2b_rd_en_esti;
end

always_ff @(posedge clk) begin
    h2b_rd_en_d2 <= h2b_rd_en_d1;
end

//===========================================================================//
// read output assignment
//===========================================================================//
always_comb begin
    for (int i=0; i<NUM_BANKS; i=i+1) begin
        h2b_rd_en[i] = int_h2b_rd_en[i];
        h2b_rd_addr[i] = int_h2b_rd_addr;
    end
end

//============================================================================//
// bypass assignment
//============================================================================//
always_comb begin
    h2b_wr_en_wsto = h2b_wr_en_esti;
    h2b_wr_strb_wsto = h2b_wr_strb_esti;
    h2b_wr_addr_wsto = h2b_wr_addr_esti;
    h2b_wr_data_wsto = h2b_wr_data_esti;
    h2b_rd_en_wsto = h2b_rd_en_esti;
    h2b_rd_addr_wsto = h2b_rd_addr_esti;
end

assign int_b2h_rd_data = int_tile_h2b_rd_en_d2 ? int_b2h_rd_data_d1[int_h2b_rd_bank_sel_d2] : b2h_rd_data_wsti;

logic [BANK_DATA_WIDTH-1:0]   b2h_rd_data_reg;
always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        b2h_rd_data_reg <= 0;
    end
    else begin
        b2h_rd_data_reg <= b2h_rd_data_esto;
    end
end

assign b2h_rd_data_esto = h2b_rd_en_d2 ? int_b2h_rd_data : b2h_rd_data_reg;

endmodule
