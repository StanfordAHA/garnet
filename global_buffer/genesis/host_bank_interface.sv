/*=============================================================================
** Module: host_bank_interface.sv
** Description:
**              Interface between host soc_ports and bank soc_ports
** Author: Taeyoung Kong
** Change history: 04/18/2019 - Implement first version
**===========================================================================*/

module host_bank_interface #(
    parameter integer NUM_BANKS = 32,
    parameter integer BANK_DATA_WIDTH = 64,
    parameter integer BANK_ADDR_WIDTH = 16
)
(

    input                           clk,
    input                           reset,
    
    input                           soc_port_wr_en,
    input  [GLB_ADDR_WIDTH-1:0]     soc_port_wr_addr,
    input  [BANK_DATA_WIDTH-1:0]    soc_port_wr_data,

    input                           soc_port_rd_en,
    input  [GLB_ADDR_WIDTH-1:0]     soc_port_rd_addr,
    output [BANK_DATA_WIDTH-1:0]    soc_port_rd_data,

    output                          host_wr_en [NUM_BANKS-1:0],
    output [BANK_DATA_WIDTH-1:0]    host_wr_data [NUM_BANKS-1:0],
    output [BANK_ADDR_WIDTH-1:0]    host_wr_addr [NUM_BANKS-1:0],

    output                          host_rd_en [NUM_BANKS-1:0],
    input  [BANK_DATA_WIDTH-1:0]    host_rd_data [NUM_BANKS-1:0],
    output [BANK_ADDR_WIDTH-1:0]    host_rd_addr [NUM_BANKS-1:0]
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
reg                         int_host_wr_en_d1 [NUM_BANKS-1:0];
reg [BANK_DATA_WIDTH-1:0]   int_host_wr_data_d1;
reg [BANK_ADDR_WIDTH-1:0]   int_host_wr_addr_d1;

//============================================================================//
// write muxing and pipelining
//============================================================================//
integer i;
always_comb begin
    for (i=0; i<NUM_BANKS; i=i+1) begin
        int_host_wr_en[i] = soc_port_wr_en && (i == soc_port_wr_addr[BANK_ADDR_WIDTH +: NUM_BANKS_WIDTH]);
    end
end
assign int_host_wr_data = soc_port_wr_data;
assign int_host_wr_addr = soc_port_wr_addr[0 +: BANK_ADDR_WIDTH];

always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        for (i=0; i<NUM_BANKS; i=i+1) begin
            int_host_wr_en_d1[i] <= 0;
        end
        int_host_wr_data_d1 <= 0;
        int_host_wr_addr_d1 <= 0;
    end
    else begin
        for (i=0; i<NUM_BANKS; i=i+1) begin
            int_host_wr_en_d1[i] <= int_host_wr_en[i];
        end
        int_host_wr_data_d1 <= int_host_wr_data;
        int_host_wr_addr_d1 <= int_host_wr_addr;
    end
end

assign host_wr_en = int_host_wr_en_d1;
always_comb begin
    for (i=0; i<NUM_BANKS; i=i+1) begin
        host_wr_addr[i] = int_host_wr_addr_d1;
    end
end
always_comb begin
    for (i=0; i<NUM_BANKS; i=i+1) begin
        host_wr_data[i] = int_host_wr_data_d1;
    end
end

//============================================================================//
// internal wire / reg declaration for write
//============================================================================//
reg                         int_host_rd_en [NUM_BANKS-1:0];
reg [BANK_ADDR_WIDTH-1:0]   int_host_rd_addr;

reg [BANK_DATA_WIDTH-1:0]   int_host_rd_data_d1 [NUM_BANKS-1:0];

reg [NUM_BANKS_WIDTH-1:0]   int_soc_port_rd_bank_sel;
reg [NUM_BANKS_WIDTH-1:0]   int_soc_port_rd_bank_sel_d1;
reg [NUM_BANKS_WIDTH-1:0]   int_soc_port_rd_bank_sel_d2;

//============================================================================//
// read muxing and pipelining
//============================================================================//
assign int_soc_port_rd_bank_sel = soc_port_rd_addr[BANK_ADDR_WIDTH +: NUM_BANKS_WIDTH];
always_comb begin
    for (i=0; i<NUM_BANKS; i=i+1) begin
        int_host_rd_en[i] = soc_port_rd_en && (i == int_soc_port_rd_bank_sel);
    end
end
assign int_host_rd_addr = soc_port_rd_addr[0 +: BANK_ADDR_WIDTH];

always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        int_soc_port_rd_bank_sel_d1 <= 0;
        int_soc_port_rd_bank_sel_d2 <= 0;
    end
    else begin
        int_soc_port_rd_bank_sel_d1 <= int_soc_port_rd_bank_sel;
        int_soc_port_rd_bank_sel_d2 <= int_soc_port_rd_bank_sel_d1;
    end
end
always_ff @(posedge clk or posedge reset) begin
    for (i=0; i<NUM_BANKS; i=i+1) begin
        if (reset) begin
            int_host_rd_data_d1[i] <= 0;
        end
        else begin
            int_host_rd_data_d1[i] <= host_rd_data[i];
        end
    end
end

always_comb begin
end

assign host_rd_en = int_host_rd_en;
always_comb begin
    for (i=0; i<NUM_BANKS; i=i+1) begin
        host_rd_addr[i] = int_host_rd_addr;
    end
end
always_comb begin
    for (i=0; i<NUM_BANKS; i=i+1) begin
        if (int_soc_port_rd_bank_sel_d2 == i) begin
            soc_port_rd_data = int_host_rd_data_d1[i];
        end
    end
end

endmodule
