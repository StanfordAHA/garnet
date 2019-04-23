/*=============================================================================
** Module: io_bank_interconnect.sv
** Description:
**              Interface between cgra io ports and bank ports
** Author: Taeyoung Kong
** Change history: 04/20/2019 - Implement first version
**===========================================================================*/

module io_bank_interconnect #(
    parameter integer NUM_BANKS = 32,
    parameter integer NUM_IO_CHANNELS = 8,
    parameter integer BANK_DATA_WIDTH = 64,
    parameter integer BANK_ADDR_WIDTH = 17,
    parameter integer CGRA_DATA_WIDTH = 16,
    parameter integer CONFIG_ADDR_WIDTH = 8,
    parameter integer CONFIG_FEATURE_WIDTH = 4,
    parameter integer CONFIG_DATA_WIDTH = 32
)
(

    input                           clk,
    input                           reset,

    input                           cgra_start_pulse,

    input                           glc_to_io_stall,
    //input                           cgra_to_io_stall [NUM_IO_CHANNELS-1:0],
    input                           cgra_to_io_wr_en [NUM_IO_CHANNELS-1:0],
    input                           cgra_to_io_rd_en [NUM_IO_CHANNELS-1:0],
    output                          io_to_cgra_rd_data_valid [NUM_IO_CHANNELS-1:0],
    input  [CGRA_DATA_WIDTH-1:0]    cgra_to_io_wr_data [NUM_IO_CHANNELS-1:0],
    output [CGRA_DATA_WIDTH-1:0]    io_to_cgra_rd_data [NUM_IO_CHANNELS-1:0],
    input  [CGRA_DATA_WIDTH-1:0]    cgra_to_io_addr_high [NUM_IO_CHANNELS-1:0],
    input  [CGRA_DATA_WIDTH-1:0]    cgra_to_io_addr_low [NUM_IO_CHANNELS-1:0],
    
    output                          io_to_bank_wr_en [NUM_BANKS-1:0],
    output [BANK_DATA_WIDTH-1:0]    io_to_bank_wr_data [NUM_BANKS-1:0],
    output [BANK_ADDR_WIDTH-1:0]    io_to_bank_wr_addr [NUM_BANKS-1:0],
    output                          io_to_bank_rd_en [NUM_BANKS-1:0],
    input  [BANK_DATA_WIDTH-1:0]    bank_to_io_rd_data [NUM_BANKS-1:0],
    output [BANK_ADDR_WIDTH-1:0]    io_to_bank_rd_addr [NUM_BANKS-1:0],

    input                           config_en,
    input                           config_wr,
    input                           config_rd,
    input  [CONFIG_ADDR_WIDTH-1:0]  config_addr,
    input  [CONFIG_DATA_WIDTH-1:0]  config_wr_data,
    output [CONFIG_DATA_WIDTH-1:0]  config_rd_data
);

//============================================================================//
// local parameter declaration
//============================================================================//
localparam integer NUM_BANKS_WIDTH = $clog2(NUM_BANKS);
localparam integer BANKS_PER_IO = $ceil(NUM_BANKS/NUM_IO_CHANNELS);
localparam integer GLB_ADDR_WIDTH = NUM_BANKS_WIDTH + BANK_ADDR_WIDTH;
localparam integer CONFIG_REG_WIDTH = CONFIG_ADDR_WIDTH - CONFIG_FEATURE_WIDTH;

//============================================================================//
// io controller instantiation
//============================================================================//
genvar i;
generate
for (i=0; i<NUM_IO_CHANNELS; i=i+1) begin: generate_io_controller
    io_controller #(
    .BANK_ADDR_WIDTH(BANK_ADDR_WIDTH),
    .BANK_DATA_WIDTH(BANK_DATA_WIDTH),
    .CGRA_DATA_WIDTH(CGRA_DATA_WIDTH)
    ) inst_io_controller (
        .clk(clk),
        .reset(reset),

        .stall(glc_to_io_stall),
        .cgra_start_pulse(cgra_start_pulse),

        .start_addr(io_ctrl_start_addr[i]),
        .num_words(io_ctrl_num_words[i]),
        .mode(io_ctrl_mode[i]),

		.cgra_to_io_wr_en(cgra_to_io_wr_en[i]),
        .cgra_to_io_rd_en(cgra_to_io_rd_en[i]),
        .io_to_cgra_rd_data_valid(io_to_cgra_rd_data_valid[i]),
        .cgra_to_io_addr_high(cgra_to_io_addr_high[i]),
        .cgra_to_io_addr_low(cgra_to_io_addr_low[i]),
        .cgra_to_io_wr_data(cgra_to_io_wr_data[i]),
        .io_to_cgra_rd_data(io_to_cgra_rd_data[i]),

        .io_to_bank_wr_en(io_wr_en[i]),
        .io_to_bank_wr_data(io_wr_data[i]),
        .io_to_bank_rd_en(io_rd_en[i]),
        .bank_to_io_rd_data(io_rd_data[i]),
        .io_to_bank_addr(io_addr[i])
    );
end
endgenerate

//============================================================================//
// internal signal
//============================================================================//
wire                        io_wr_en [NUM_IO_CHANNELS-1:0];
wire                        io_rd_en [NUM_IO_CHANNELS-1:0];
wire [BANK_DATA_WIDTH-1:0]  io_wr_data [NUM_IO_CHANNELS-1:0];
wire [BANK_DATA_WIDTH-1:0]  io_rd_data [NUM_IO_CHANNELS-1:0];
wire [GLB_ADDR_WIDTH-1:0]   io_addr [NUM_IO_CHANNELS-1:0];

// The number of switching mux is one less than the number of IO channels
reg [`$num_io_channels-2`:0]   switch_sel;
reg [GLB_ADDR_WIDTH-1:0]    io_ctrl_start_addr [`$num_io_channels-1`:0];
reg [GLB_ADDR_WIDTH-1:0]    io_ctrl_num_words [`$num_io_channels-1`:0];
reg [1:0]                   io_ctrl_mode [`$num_io_channels-1`:0];

//============================================================================//
// configuration
//============================================================================//
integer j, k;

wire [CONFIG_FEATURE_WIDTH-1:0] config_feature_addr;
wire [CONFIG_REG_WIDTH-1:0]     config_reg_addr;
reg                             config_en_io_ctrl [NUM_IO_CHANNELS-1:0];
reg                             config_en_io_int;

assign config_feature_addr = config_addr[CONFIG_ADDR_WIDTH-1 -: CONFIG_FEATURE_WIDTH];
assign config_reg_addr = config_addr[CONFIG_REG_WIDTH-1:0];
always_comb begin
    for(j=0; j<NUM_IO_CHANNELS; j=j+1) begin
        config_en_io_ctrl[j] = config_en && (config_feature_addr == j);
    end
    config_en_io_int = config_en && (config_feature_addr == NUM_IO_CHANNELS);
end

always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        switch_sel <= 0;
    end
    else begin
        if (config_en_io_int && config_wr) begin
            case (config_reg_addr)
                0: switch_sel <= config_wr_data;
            endcase
        end
    end
end

always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        for(j=0; j<NUM_IO_CHANNELS; j=j+1) begin
            io_ctrl_mode[j] <= 0;
            io_ctrl_start_addr[j] <= 0;
            io_ctrl_num_words[j] <= 0;
        end
    end
    else begin
        for(j=0; j<NUM_IO_CHANNELS; j=j+1) begin
            if (config_en_io_ctrl[j] && config_wr) begin
                case (config_reg_addr)
                    0: io_ctrl_mode[j] <= config_wr_data;
                    1: io_ctrl_start_addr[j] <= config_wr_data;
                    2: io_ctrl_num_words[j] <= config_wr_data;
                endcase
            end
        end
    end
end

always_comb begin
    config_rd_data = 0;
    if (config_en_io_int && config_rd) begin
        case (config_reg_addr)
            0: config_rd_data = switch_sel;
            default: config_rd_data = 0;
        endcase
    end
    else begin
        for(j=0; j<NUM_IO_CHANNELS; j=j+1) begin
            if (config_en_io_ctrl[j] && config_rd) begin
                case (config_reg_addr)
                    0: config_rd_data = io_ctrl_mode[j];
                    1: config_rd_data = io_ctrl_start_addr[j];
                    2: config_rd_data = io_ctrl_num_words[j];
                    default: config_rd_data = 0;
                endcase
            end
        end
    end
end

//============================================================================//
// address channel interconnection network with pipeline
//============================================================================//

reg [GLB_ADDR_WIDTH-1:0] io_addr_int [NUM_IO_CHANNELS-1:0];
reg [GLB_ADDR_WIDTH-1:0] bank_addr_int [NUM_BANKS-1:0];

always_comb begin
    io_addr_int[0] = io_addr[0];
    for (j=1; j<NUM_IO_CHANNELS; j=j+1) begin
        io_addr_int[j] = switch_sel[j-1] ? io_addr[j] : io_addr_int[j-1];
    end
end

always_comb begin
    for (k=0; k<NUM_BANKS; k=k+1) begin
        bank_addr_int[k] = io_addr_int[k/BANKS_PER_IO];
    end
end

//============================================================================//
// write channel interconnection network with pipeline
//============================================================================//
reg                         io_wr_en_int [NUM_IO_CHANNELS-1:0];
reg                         bank_wr_en_int [NUM_BANKS-1:0];
reg [BANK_DATA_WIDTH-1:0]   io_wr_data_int [NUM_IO_CHANNELS-1:0];
reg [BANK_DATA_WIDTH-1:0]   bank_wr_data_int [NUM_BANKS-1:0];
always_comb begin
    io_wr_en_int[0] = io_wr_en[0];
    for (j=1; j<NUM_IO_CHANNELS; j=j+1) begin
        io_wr_en_int[j] = switch_sel[j-1] ? io_wr_en[j] : io_wr_en_int[j-1];
    end
end

always_comb begin
    for (k=0; k<NUM_BANKS; k=k+1) begin
        bank_wr_en_int[k] = io_wr_en_int[k/BANKS_PER_IO] 
                            && (bank_addr_int[k][BANK_ADDR_WIDTH +: NUM_BANKS_WIDTH] == k);  
    end
end

always_comb begin
    io_wr_data_int[0] = io_wr_data[0];
    for (j=1; j<NUM_IO_CHANNELS; j=j+1) begin
        io_wr_data_int[j] = switch_sel[j-1] ? io_wr_data[j] : io_wr_data_int[j-1];
    end
end

always_comb begin
    for (k=0; k<NUM_BANKS; k=k+1) begin
        bank_wr_data_int[k] = io_wr_data_int[k/BANKS_PER_IO]; 
    end
end

//============================================================================//
// read channel interconnection network with pipeline
//============================================================================//
reg                         io_rd_en_int [NUM_IO_CHANNELS-1:0];
reg                         bank_rd_en_int [NUM_BANKS-1:0];
reg                         bank_rd_en_int_d1 [NUM_BANKS-1:0];
reg                         bank_rd_en_int_d2 [NUM_BANKS-1:0];
reg [BANK_DATA_WIDTH-1:0]   io_rd_data_int [NUM_IO_CHANNELS-1:0];
reg [BANK_DATA_WIDTH-1:0]   bank_rd_data_int [NUM_BANKS-1:0];
reg [BANK_DATA_WIDTH-1:0]   bank_to_io_rd_data_d1 [NUM_BANKS-1:0];

always_comb begin
    io_rd_en_int[0] = io_rd_en[0];
    for (j=1; j<NUM_IO_CHANNELS; j=j+1) begin
        io_rd_en_int[j] = switch_sel[j-1] ? io_rd_en[j] : io_rd_en_int[j-1];
    end
end

always_comb begin
    for (k=0; k<NUM_BANKS; k=k+1) begin
        bank_rd_en_int[k] = io_rd_en_int[k/BANKS_PER_IO] 
                            && (bank_addr_int[k][BANK_ADDR_WIDTH +: NUM_BANKS_WIDTH] == k);  
    end
end

always_ff @(posedge clk or posedge reset) begin
    for (k=0; k<NUM_BANKS; k=k+1) begin
        if (reset) begin
            bank_rd_en_int_d1[k] <= 0;
            bank_rd_en_int_d2[k] <= 0;
        end
        else begin
            bank_rd_en_int_d1[k] <= bank_rd_en_int[k];
            bank_rd_en_int_d2[k] <= bank_rd_en_int_d1[k];
        end
    end
end

always_ff @(posedge clk or posedge reset) begin
    for (k=0; k<NUM_BANKS; k=k+1) begin
        if (reset) begin
            bank_to_io_rd_data_d1[k] <= 0;
        end
        else begin
            bank_to_io_rd_data_d1[k] <= bank_to_io_rd_data[k]; 
        end
    end
end

always_comb begin
    bank_rd_data_int[NUM_BANKS-1] = bank_rd_en_int_d2[NUM_BANKS-1] ? bank_to_io_rd_data_d1[NUM_BANKS-1] : 0;
    for (k=0; k<NUM_BANKS-1; k=k+1) begin
        bank_rd_data_int[k] = bank_rd_en_int_d2[k] ? bank_to_io_rd_data_d1[k] : bank_rd_data_int[k+1];
    end
end

always_comb begin
    for (j=0; j<NUM_IO_CHANNELS; j=j+1) begin
        io_rd_data_int[j] = bank_rd_data_int[j*BANKS_PER_IO];
    end
end

assign io_rd_data = io_rd_data_int;

//============================================================================//
// output assignment
//============================================================================//
assign io_to_bank_wr_en = bank_wr_en_int;
assign io_to_bank_wr_data = bank_wr_data_int;

always_comb begin
    for (k=0; k<NUM_BANKS; k=k+1) begin
        io_to_bank_wr_addr[k] = bank_addr_int[k][BANK_ADDR_WIDTH-1:0];
        io_to_bank_rd_addr[k] = bank_addr_int[k][BANK_ADDR_WIDTH-1:0];
    end
end
assign io_to_bank_rd_en = bank_rd_en_int;

endmodule
