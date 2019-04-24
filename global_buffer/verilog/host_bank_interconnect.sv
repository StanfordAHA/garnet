/*=============================================================================
** Module: host_bank_interconnect.sv
** Description:
**              Interface between host soc_ports and bank soc_ports
** Author: Taeyoung Kong
** Change history: 04/18/2019 - Implement first version
**===========================================================================*/

module host_bank_interconnect #(
    parameter integer NUM_BANKS = 32,
    parameter integer BANK_DATA_WIDTH = 64,
    parameter integer BANK_ADDR_WIDTH = 16
)
(

    input                           clk,
    
    input                           host_wr_en,
    input  [GLB_ADDR_WIDTH-1:0]     host_wr_addr,
    input  [BANK_DATA_WIDTH-1:0]    host_wr_data,

    input                           host_rd_en,
    input  [GLB_ADDR_WIDTH-1:0]     host_rd_addr,
    output [BANK_DATA_WIDTH-1:0]    host_rd_data,

    output                          host_to_bank_wr_en [NUM_BANKS-1:0],
    output [BANK_DATA_WIDTH-1:0]    host_to_bank_wr_data [NUM_BANKS-1:0],
    output [BANK_ADDR_WIDTH-1:0]    host_to_bank_wr_addr [NUM_BANKS-1:0],

    output                          host_to_bank_rd_en [NUM_BANKS-1:0],
    input  [BANK_DATA_WIDTH-1:0]    bank_to_host_rd_data [NUM_BANKS-1:0],
    output [BANK_ADDR_WIDTH-1:0]    host_to_bank_rd_addr [NUM_BANKS-1:0]
);

//============================================================================//
// local parameter declaration
//============================================================================//
localparam integer NUM_BANKS_WIDTH = $clog2(NUM_BANKS);
localparam integer GLB_ADDR_WIDTH = NUM_BANKS_WIDTH + BANK_ADDR_WIDTH;

//============================================================================//
// internal wire / reg declaration for write
//============================================================================//
reg                         int_host_wr_en [NUM_BANKS-1:0];
reg [BANK_DATA_WIDTH-1:0]   int_host_wr_data;
reg [BANK_ADDR_WIDTH-1:0]   int_host_wr_addr;

//============================================================================//
// write muxing
//============================================================================//
integer i;
always_comb begin
    for (i=0; i<NUM_BANKS; i=i+1) begin
        int_host_wr_en[i] = host_wr_en && (i == host_wr_addr[BANK_ADDR_WIDTH +: NUM_BANKS_WIDTH]);
    end
end
assign int_host_wr_data = host_wr_data;
assign int_host_wr_addr = host_wr_addr[0 +: BANK_ADDR_WIDTH];
assign host_to_bank_wr_en = int_host_wr_en;

always_comb begin
    for (i=0; i<NUM_BANKS; i=i+1) begin
        host_to_bank_wr_addr[i] = int_host_wr_addr;
    end
end
always_comb begin
    for (i=0; i<NUM_BANKS; i=i+1) begin
        host_to_bank_wr_data[i] = int_host_wr_data;
    end
end

//============================================================================//
// internal wire / reg declaration for write
//============================================================================//
reg                         int_host_rd_en [NUM_BANKS-1:0];
reg [BANK_ADDR_WIDTH-1:0]   int_host_rd_addr;

reg [BANK_DATA_WIDTH-1:0]   int_host_rd_data;
reg [BANK_DATA_WIDTH-1:0]   int_host_rd_data_d1 [NUM_BANKS-1:0];

reg [NUM_BANKS_WIDTH-1:0]   int_host_rd_bank_sel;
reg [NUM_BANKS_WIDTH-1:0]   int_host_rd_bank_sel_d1;
reg [NUM_BANKS_WIDTH-1:0]   int_host_rd_bank_sel_d2;

//============================================================================//
// read muxing and pipelining
//============================================================================//
assign int_host_rd_bank_sel = host_rd_addr[BANK_ADDR_WIDTH +: NUM_BANKS_WIDTH];
always_comb begin
    for (i=0; i<NUM_BANKS; i=i+1) begin
        int_host_rd_en[i] = host_rd_en && (i == int_host_rd_bank_sel);
    end
end
assign int_host_rd_addr = host_rd_addr[0 +: BANK_ADDR_WIDTH];

always_ff @(posedge clk) begin
    int_host_rd_bank_sel_d1 <= int_host_rd_bank_sel;
    int_host_rd_bank_sel_d2 <= int_host_rd_bank_sel_d1;
end
always_ff @(posedge clk) begin
    for (i=0; i<NUM_BANKS; i=i+1) begin
        int_host_rd_data_d1[i] <= bank_to_host_rd_data[i];
    end
end

assign host_to_bank_rd_en = int_host_rd_en;
always_comb begin
    for (i=0; i<NUM_BANKS; i=i+1) begin
        host_to_bank_rd_addr[i] = int_host_rd_addr;
    end
end
always_comb begin
    for (i=0; i<NUM_BANKS; i=i+1) begin
        if (int_host_rd_bank_sel_d2 == i) begin
            int_host_rd_data = int_host_rd_data_d1[i];
        end
    end
end


//===========================================================================//
// rd_data output assignment
//===========================================================================//
reg host_rd_en_d1;
reg host_rd_en_d2;
reg [BANK_DATA_WIDTH-1:0]   host_rd_data_reg;

always @(posedge clk) begin
    host_rd_en_d1 <= host_rd_en;
    host_rd_en_d2 <= host_rd_en_d1;
    host_rd_data_reg <= host_rd_data;
end

assign host_rd_data = host_rd_en_d2 ? int_host_rd_data : host_rd_data_reg;

endmodule
