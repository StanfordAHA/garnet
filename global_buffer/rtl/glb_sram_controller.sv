/*=============================================================================
** Module: glb_sram_controller.sv
** Description:
**              sram controller
** Author: Taeyoung Kong
** Change history:  10/08/2019 - Implement first version of sram controller
**===========================================================================*/
import global_buffer_pkg::*;

module glb_sram_controller (
    input  logic                                                clk,
    input  logic                                                reset,

    input  logic                                                ren,
    input  logic                                                wen,

    input  logic [BANK_ADDR_WIDTH-1:0]                          addr,
    input  logic [BANK_DATA_WIDTH-1:0]                          data_in,
    input  logic [BANK_DATA_WIDTH-1:0]                          data_in_bit_sel,
    output logic [BANK_DATA_WIDTH-1:0]                          data_out,

    // input  logic                                                config_en,
    // input  logic                                                config_wr,
    // input  logic                                                config_rd,
    // input  logic [BANK_ADDR_WIDTH-1:0]                          config_addr,
    // input  logic [CONFIG_DATA_WIDTH-1:0]                        config_wr_data,
    // output logic [CONFIG_DATA_WIDTH-1:0]                        config_rd_data,

    output logic [BANK_DATA_WIDTH-1:0]                          sram_to_mem_data,
    output logic [BANK_DATA_WIDTH-1:0]                          sram_to_mem_bit_sel,
    output logic                                                sram_to_mem_cen,
    output logic                                                sram_to_mem_wen,
    output logic [BANK_ADDR_WIDTH-BANK_ADDR_BYTE_OFFSET-1:0]    sram_to_mem_addr,
    input  logic [BANK_DATA_WIDTH-1:0]                          mem_to_sram_data
);

//===========================================================================//
// signal declaration
//===========================================================================//
logic sram_to_mem_ren;
logic sram_to_mem_ren_delay;
logic [BANK_DATA_WIDTH-1:0] data_out_reg;

//===========================================================================//
// sram-memory interface
//===========================================================================//
always_comb begin
    // if (config_en && config_wr) begin
    //     // Configuration assumes that 2 * CONFIG_DATA_WIDTH >= BANK_DATA_WIDTH
    //     assert (CONFIG_DATA_WIDTH * 2 < BANK_DATA_WIDTH)
    //     else $error("Configuration data width must be at least half of the bank data width");
    //     if (config_addr[BANK_ADDR_BYTE_OFFSET-1] == 0) begin
    //         // configuring LSB bits
    //         sram_to_mem_wen = 1;
    //         sram_to_mem_ren = 0;
    //         sram_to_mem_cen = 1;
    //         sram_to_mem_addr = config_addr[BANK_ADDR_BYTE_OFFSET +: BANK_ADDR_WIDTH-BANK_ADDR_BYTE_OFFSET];
    //         sram_to_mem_data = {{{BANK_DATA_WIDTH-CONFIG_DATA_WIDTH}{1'b0}}, config_wr_data};
    //         sram_to_mem_bit_sel = {{{BANK_DATA_WIDTH-CONFIG_DATA_WIDTH}{1'b0}}, {CONFIG_DATA_WIDTH{1'b1}}};
    //         config_rd_data = 0;
    //     end
    //     else begin
    //         // configuring MSB bits
    //         sram_to_mem_wen = 1;
    //         sram_to_mem_ren = 0;
    //         sram_to_mem_cen = 1;
    //         sram_to_mem_addr = config_addr[BANK_ADDR_BYTE_OFFSET +: BANK_ADDR_WIDTH-BANK_ADDR_BYTE_OFFSET];
    //         sram_to_mem_data = {config_wr_data[BANK_DATA_WIDTH-CONFIG_DATA_WIDTH-1:0], {CONFIG_DATA_WIDTH{1'b0}}};
    //         sram_to_mem_bit_sel = {{{BANK_DATA_WIDTH-CONFIG_DATA_WIDTH}{1'b1}}, {CONFIG_DATA_WIDTH{1'b0}}};
    //         config_rd_data = 0;
    //     end
    // end
    // else if (config_en && config_rd) begin
    //     sram_to_mem_wen = 0;
    //     sram_to_mem_ren = 1;
    //     sram_to_mem_cen = 1;
    //     sram_to_mem_addr = config_addr[BANK_ADDR_BYTE_OFFSET +: BANK_ADDR_WIDTH-BANK_ADDR_BYTE_OFFSET];
    //     sram_to_mem_data = 0;
    //     sram_to_mem_bit_sel = 0;
    //     if (config_addr[BANK_ADDR_BYTE_OFFSET-1] == 0) begin
    //         config_rd_data = data_out[0 +: CONFIG_DATA_WIDTH];
    //     end
    //     else begin
    //         config_rd_data = data_out[BANK_DATA_WIDTH-1 -: CONFIG_DATA_WIDTH];
    //     end
    // end
    // else begin
        sram_to_mem_wen = wen;
        sram_to_mem_ren = ren;
        sram_to_mem_cen = wen | ren;
        sram_to_mem_addr = addr[BANK_ADDR_BYTE_OFFSET +: BANK_ADDR_WIDTH-BANK_ADDR_BYTE_OFFSET];
        sram_to_mem_data = data_in;
        sram_to_mem_bit_sel = data_in_bit_sel;
    //     config_rd_data = 0;
    // end
end

//===========================================================================//
// output assignment
//===========================================================================//
always_ff @(posedge clk or posedge reset) begin
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
