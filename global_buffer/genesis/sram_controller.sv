/*=============================================================================
** Module: sram_controller.sv
** Description:
**              sram controller
** Author: Taeyoung Kong
** Change history:  04/10/2019 - Implement first version of sram controller
**===========================================================================*/

module sram_controller #(
    parameter integer BANK_DATA_WIDTH = 64,
    parameter integer BANK_ADDR_WIDTH = 16,
    parameter integer CONFIG_DATA_WIDTH = 32
)
(
    input wire                                      clk,
    input wire                                      reset,

    input wire                                      ren,
    input wire                                      wen,

    input wire  [BANK_ADDR_WIDTH-1:0]               addr,
    input wire  [BANK_DATA_WIDTH-1:0]               data_in,
    output wire [BANK_DATA_WIDTH-1:0]               data_out,

    input wire                                      config_en,
    input wire                                      config_wr,
    input wire                                      config_rd,
    input wire  [BANK_ADDR_WIDTH-1:0]               config_addr,
    input wire  [CONFIG_DATA_WIDTH-1:0]             config_wr_data,
    output wire [CONFIG_DATA_WIDTH-1:0]             config_rd_data,

    output wire [BANK_DATA_WIDTH-1:0]               sram_to_mem_data,
    output wire                                     sram_to_mem_cen,
    output wire                                     sram_to_mem_wen,
    output wire [BANK_ADDR_WIDTH-ADDR_OFFSET-1:0]   sram_to_mem_addr,
    input wire  [BANK_DATA_WIDTH-1:0]               mem_to_sram_data
);

//===========================================================================//
// local parameter declaration
//===========================================================================//
localparam integer ADDR_OFFSET = $clog2(BANK_DATA_WIDTH/8);

//===========================================================================//
// signal declaration
//===========================================================================//
wire sram_to_mem_ren;
reg sram_to_mem_ren_delay;
reg [BANK_DATA_WIDTH-1:0] data_out_reg;

//===========================================================================//
// sram configuration buffer
//===========================================================================//
reg config_wr_buffed;
reg [CONFIG_DATA_WIDTH-1:0] config_wr_buffer;
always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        config_wr_buffed <= 0;
        config_wr_buffer <= 0;
    end
    else if (config_en && config_wr) begin
        if (config_addr[ADDR_OFFSET-1] == 0) begin
            config_wr_buffed <= 1;
            config_wr_buffer <= config_wr_data;
        end
        else begin
            config_wr_buffed <= 0;
            config_wr_buffer <= 0;
        end
    end
end

//===========================================================================//
// sram-memory interface
//===========================================================================//
always_comb begin
    if (config_en && config_wr) begin
        if (config_wr_buffed) begin
            sram_to_mem_wen = 1;
            sram_to_mem_ren = 0;
            sram_to_mem_cen = 1;
            sram_to_mem_addr = config_addr[ADDR_OFFSET +: BANK_ADDR_WIDTH-ADDR_OFFSET];
            sram_to_mem_data = {config_wr_data, config_wr_buffer};
            config_rd_data = 0;
        end
        else begin
            sram_to_mem_wen = 0;
            sram_to_mem_ren = 0;
            sram_to_mem_cen = 0;
            sram_to_mem_addr = 0;
            sram_to_mem_data = 0;
            config_rd_data = 0;
        end
    end
    else if (config_en && config_rd) begin
        sram_to_mem_wen = 0;
        sram_to_mem_ren = 1;
        sram_to_mem_cen = 1;
        sram_to_mem_addr = config_addr[ADDR_OFFSET +: BANK_ADDR_WIDTH-ADDR_OFFSET];
        sram_to_mem_data = 0;
        if (config_addr[ADDR_OFFSET-1] == 0) begin
            config_rd_data = data_out[0 +: CONFIG_DATA_WIDTH];
        end
        else begin
            config_rd_data = data_out[BANK_DATA_WIDTH-1 -: CONFIG_DATA_WIDTH];
        end
    end
    else begin
        sram_to_mem_wen = wen;
        sram_to_mem_ren = ren;
        sram_to_mem_cen = wen | ren;
        sram_to_mem_addr = addr[ADDR_OFFSET +: BANK_ADDR_WIDTH-ADDR_OFFSET];
        sram_to_mem_data = data_in;
        config_rd_data = 0;
    end
end

//===========================================================================//
// output assignment
//===========================================================================//
always @(posedge clk or posedge reset) begin
    if (reset) begin
        sram_to_mem_ren_delay <= 0;
        data_out_reg <= 0;
    end
    else begin
        sram_to_mem_ren_delay <= sram_to_mem_ren;
        data_out_reg <= data_out;
    end
end
assign data_out = sram_to_mem_ren_delay ? mem_to_sram_data : data_out_reg;

endmodule
