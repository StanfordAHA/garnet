/*=============================================================================
** Module: ps_interconnect.sv
** Description:
**              Interconnect for processor data
** Author: Taeyoung Kong
** Change history: 10/07/2019 - Implement first version
**===========================================================================*/
import global_buffer_pkg::*;

module ps_interconnect (
    input  logic                            clk,
    input  logic                            reset,
    input  logic [TILE_SEL_ADDR_WIDTH-1:0]  glb_tile_col,
    
    // East
    input  logic                            ps_wr_en_esti,
    input  logic [BANK_DATA_WIDTH/8-1:0]    ps_wr_strb_esti,
    input  logic [GLB_ADDR_WIDTH-1:0]       ps_wr_addr_esti,
    input  logic [BANK_DATA_WIDTH-1:0]      ps_wr_data_esti,
    input  logic                            ps_rd_en_esti,
    input  logic [GLB_ADDR_WIDTH-1:0]       ps_rd_addr_esti,
    output logic [BANK_DATA_WIDTH-1:0]      ps_rd_data_esto,

    // West
    output logic                            ps_wr_en_wsto,
    output logic [BANK_DATA_WIDTH/8-1:0]    ps_wr_strb_wsto,
    output logic [GLB_ADDR_WIDTH-1:0]       ps_wr_addr_wsto,
    output logic [BANK_DATA_WIDTH-1:0]      ps_wr_data_wsto,
    output logic                            ps_rd_en_wsto,
    output logic [GLB_ADDR_WIDTH-1:0]       ps_rd_addr_wsto,
    input  logic [BANK_DATA_WIDTH-1:0]      ps_rd_data_wsti,

    // Bank
    output logic                            bank_wr_en [0:NUM_BANKS-1],
    output logic [BANK_DATA_WIDTH-1:0]      bank_wr_data [0:NUM_BANKS-1],
    output logic [BANK_DATA_WIDTH-1:0]      bank_wr_data_bit_sel [0:NUM_BANKS-1],
    output logic [BANK_ADDR_WIDTH-1:0]      bank_wr_addr [0:NUM_BANKS-1],
    output logic                            bank_rd_en [0:NUM_BANKS-1],
    input  logic [BANK_DATA_WIDTH-1:0]      bank_rd_data [0:NUM_BANKS-1],
    output logic [BANK_ADDR_WIDTH-1:0]      bank_rd_addr [0:NUM_BANKS-1]
);

//============================================================================//
// internal logic declaration for write
//============================================================================//
logic                           int_tile_ps_wr_en;
logic [BANK_SEL_ADDR_WIDTH-1:0] int_ps_wr_bank_sel;
logic                           int_bank_ps_wr_en [0:NUM_BANKS-1];
logic [BANK_DATA_WIDTH-1:0]     int_bank_ps_wr_data;
logic [BANK_DATA_WIDTH-1:0]     int_bank_ps_wr_data_bit_sel;
logic [BANK_ADDR_WIDTH-1:0]     int_bank_ps_wr_addr;

logic                           int_bank_ps_wr_en_d1 [0:NUM_BANKS-1];
logic [BANK_DATA_WIDTH-1:0]     int_bank_ps_wr_data_d1;
logic [BANK_DATA_WIDTH-1:0]     int_bank_ps_wr_data_bit_sel_d1;
logic [BANK_ADDR_WIDTH-1:0]     int_bank_ps_wr_addr_d1;

//============================================================================//
// write muxing
//============================================================================//
assign int_tile_ps_wr_en = ps_wr_en_esti && (glb_tile_col == ps_wr_addr_esti[BANK_ADDR_WIDTH + BANK_SEL_ADDR_WIDTH +: TILE_SEL_ADDR_WIDTH]);
assign int_ps_wr_bank_sel = ps_wr_addr_esti[BANK_ADDR_WIDTH +: BANK_SEL_ADDR_WIDTH];
always_comb begin
    for (int i=0; i<NUM_BANKS; i=i+1) begin
       int_bank_ps_wr_en[i] = int_tile_ps_wr_en && (i == int_ps_wr_bank_sel);
    end
end
assign int_bank_ps_wr_data = ps_wr_data_esti;
assign int_bank_ps_wr_addr = ps_wr_addr_esti[0 +: BANK_ADDR_WIDTH];
always_comb begin
    for (int i=0; i<BANK_DATA_WIDTH/8; i=i+1) begin
        // Byte-addressable
        int_bank_ps_wr_data_bit_sel[i*8 +: 8] = {8{ps_wr_strb_esti[i]}};
    end
end

//============================================================================//
// write pipelining
//============================================================================//
always_ff @ (posedge clk) begin
    for (int i=0; i<NUM_BANKS; i=i+1) begin
        int_bank_ps_wr_en_d1[i] <= int_bank_ps_wr_en[i];
    end
    int_bank_ps_wr_addr_d1 <= int_bank_ps_wr_addr;
    int_bank_ps_wr_data_d1 <= int_bank_ps_wr_data;
    int_bank_ps_wr_data_bit_sel_d1 <= int_bank_ps_wr_data_bit_sel;
end

//============================================================================//
// write output assignment
//============================================================================//
always_comb begin
    for (int i=0; i<NUM_BANKS; i=i+1) begin
        bank_wr_en[i] = int_bank_ps_wr_en_d1[i];
        bank_wr_addr[i] = int_bank_ps_wr_addr_d1;
        bank_wr_data[i] = int_bank_ps_wr_data_d1;
        bank_wr_data_bit_sel[i] = int_bank_ps_wr_data_bit_sel_d1;
    end
end

//============================================================================//
// internal logic declaration for read
//============================================================================//
logic                           int_tile_ps_rd_en;
logic                           int_bank_ps_rd_en [0:NUM_BANKS-1];
logic [BANK_SEL_ADDR_WIDTH-1:0] int_ps_rd_bank_sel;
logic [BANK_DATA_WIDTH-1:0]     int_bank_ps_rd_data;
logic [BANK_ADDR_WIDTH-1:0]     int_bank_ps_rd_addr;

logic                           int_bank_ps_rd_en_d1 [0:NUM_BANKS-1];
logic [BANK_DATA_WIDTH-1:0]     int_bank_ps_rd_data_d1 [0:NUM_BANKS-1];
logic [BANK_ADDR_WIDTH-1:0]     int_bank_ps_rd_addr_d1;
logic                           int_tile_ps_rd_en_d1;
logic [BANK_SEL_ADDR_WIDTH-1:0] int_ps_rd_bank_sel_d1;

logic                           int_tile_ps_rd_en_d2;
logic [BANK_SEL_ADDR_WIDTH-1:0] int_ps_rd_bank_sel_d2;

logic                           ps_rd_en_d1;
logic                           ps_rd_en_d2;

//============================================================================//
// read muxing
//============================================================================//
assign int_tile_ps_rd_en = ps_rd_en_esti && (glb_tile_col == ps_rd_addr_esti[BANK_ADDR_WIDTH + BANK_SEL_ADDR_WIDTH +: TILE_SEL_ADDR_WIDTH]);
assign int_ps_rd_bank_sel = ps_rd_addr_esti[BANK_ADDR_WIDTH +: BANK_SEL_ADDR_WIDTH];
always_comb begin
    for (int i=0; i<NUM_BANKS; i=i+1) begin
        int_bank_ps_rd_en[i] = int_tile_ps_rd_en && (i == int_ps_rd_bank_sel);
    end
end

assign int_bank_ps_rd_addr = ps_rd_addr_esti[0 +: BANK_ADDR_WIDTH];


//============================================================================//
// read pipelining
//============================================================================//
always_ff @(posedge clk) begin
    int_ps_rd_bank_sel_d1 <= int_ps_rd_bank_sel;
    int_tile_ps_rd_en_d1 <= int_tile_ps_rd_en;
end

always_ff @(posedge clk) begin
    int_ps_rd_bank_sel_d2 <= int_ps_rd_bank_sel_d1;
    int_tile_ps_rd_en_d2 <= int_tile_ps_rd_en_d1;
end

always_ff @ (posedge clk) begin
    for (int i=0; i<NUM_BANKS; i=i+1) begin
        int_bank_ps_rd_en_d1[i] <= int_bank_ps_rd_en[i];
    end
    int_bank_ps_rd_addr_d1 <= int_bank_ps_rd_addr;
end

always_ff @(posedge clk) begin
    for (int i=0; i<NUM_BANKS; i=i+1) begin
        int_bank_ps_rd_data_d1[i] <= bank_rd_data[i];
    end
end

always_ff @(posedge clk) begin
    ps_rd_en_d1 <= ps_rd_en_esti;
end

always_ff @(posedge clk) begin
    ps_rd_en_d2 <= ps_rd_en_d1;
end

//===========================================================================//
// rd_data output assignment
//===========================================================================//
assign int_ps_rd_data = int_tile_ps_rd_en_d2 ? int_bank_ps_rd_data_d1[int_ps_rd_bank_sel_d2] : ps_rd_data_wsti;

logic [BANK_DATA_WIDTH-1:0]   ps_rd_data_reg;
always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        ps_rd_data_reg <= 0;
    end
    else begin
        ps_rd_data_reg <= ps_rd_data_esto;
    end
end

assign ps_rd_data_esto = ps_rd_en_d2 ? int_ps_rd_data : ps_rd_data_reg;

//============================================================================//
// bypass assignment
//============================================================================//
always_comb begin
    ps_wr_en_wsto = ps_wr_en_esti;
    ps_wr_strb_wsto = ps_wr_strb_esti;
    ps_wr_addr_wsto = ps_wr_addr_esti;
    ps_wr_data_wsto = ps_wr_data_esti;
    ps_rd_en_wsto = ps_rd_en_esti;
    ps_rd_addr_wsto = ps_rd_addr_esti;
end

endmodule
