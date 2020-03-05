/*=============================================================================
** Module: glb_bank_cfg_controller.sv
** Description:
**              bank controller coordinates host-cgra read/write.
**              host read/write has priority
** Author: Taeyoung Kong
** Change history:  10/08/2019 - Implement first version of bank controller
**===========================================================================*/
import global_buffer_pkg::*;

module glb_bank_cfg_controller (
    input  logic                    clk,
    input  logic                    reset,

    // interface with host
    // input  logic                          host_wr_en,
    // input  logic  [BANK_ADDR_WIDTH-1:0]   host_wr_addr,
    // input  logic  [BANK_DATA_WIDTH-1:0]   host_wr_data,
    // input  logic  [BANK_DATA_WIDTH-1:0]   host_wr_data_bit_sel,

    // input  logic                          host_rd_en,
    // input  logic  [BANK_ADDR_WIDTH-1:0]   host_rd_addr,
    // output logic  [BANK_DATA_WIDTH-1:0]   host_rd_data,

    // interface with cgra
    input  logic                          cgra_wr_en,
    input  logic  [BANK_ADDR_WIDTH-1:0]   cgra_wr_addr,
    input  logic  [BANK_DATA_WIDTH-1:0]   cgra_wr_data,
    input  logic  [BANK_DATA_WIDTH-1:0]   cgra_wr_data_bit_sel,

    input  logic                          cgra_rd_en,
    input  logic  [BANK_ADDR_WIDTH-1:0]   cgra_rd_addr,
    output logic  [BANK_DATA_WIDTH-1:0]   cgra_rd_data,

    // interface with cfg
    // input  logic                          cfg_rd_en,
    // input  logic  [BANK_ADDR_WIDTH-1:0]   cfg_rd_addr,
    // output logic  [BANK_DATA_WIDTH-1:0]   cfg_rd_data,

    // interface with memory core
    output logic                          mem_rd_en,
    output logic                          mem_wr_en,
    output logic  [BANK_ADDR_WIDTH-1:0]   mem_addr,
    output logic  [BANK_DATA_WIDTH-1:0]   mem_data_in,
    output logic  [BANK_DATA_WIDTH-1:0]   mem_data_in_bit_sel,
    input  logic  [BANK_DATA_WIDTH-1:0]   mem_data_out
);

//===========================================================================//
// signal declaration
//===========================================================================//
logic cgra_rd_en_reg;
logic host_rd_en_reg;
logic cfg_rd_en_reg;
logic [BANK_DATA_WIDTH-1:0] cgra_rd_data_reg;
logic [BANK_DATA_WIDTH-1:0] host_rd_data_reg;
logic [BANK_DATA_WIDTH-1:0] cfg_rd_data_reg;

//===========================================================================//
// Set mem_wr_en and mem_data_in output
//===========================================================================//
always_comb begin
    // if (host_wr_en) begin
    //     mem_wr_en = 1;
    //     mem_rd_en = 0;
    //     mem_data_in = host_wr_data;
    //     mem_data_in_bit_sel = host_wr_data_bit_sel;
    //     mem_addr = host_wr_addr;
    // end
    // else if (host_rd_en) begin
    //     mem_wr_en = 0;
    //     mem_data_in_bit_sel = {BANK_DATA_WIDTH{1'b0}};
    //     mem_rd_en = 1;
    //     mem_data_in = 0;
    //     mem_addr = host_rd_addr;
    // end
    // else if (cfg_rd_en) begin
    //     mem_wr_en = 0;
    //     mem_data_in_bit_sel = {BANK_DATA_WIDTH{1'b0}};
    //     mem_rd_en = 1;
    //     mem_data_in = 0;
    //     mem_addr = cfg_rd_addr;
    // end
    if (cgra_wr_en) begin
        mem_wr_en = 1;
        mem_data_in_bit_sel = cgra_wr_data_bit_sel;
        mem_rd_en = 0;
        mem_data_in = cgra_wr_data;
        mem_addr = cgra_wr_addr;
    end
    else if (cgra_rd_en) begin
        mem_wr_en = 0;
        mem_data_in_bit_sel = {BANK_DATA_WIDTH{1'b0}};
        mem_rd_en = 1;
        mem_data_in = 0;
        mem_addr = cgra_rd_addr;
    end
    else begin
        mem_wr_en = 0;
        mem_data_in_bit_sel = {BANK_DATA_WIDTH{1'b0}};
        mem_rd_en = 0;
        mem_data_in = 0;
        mem_addr = 0;
    end
end

//===========================================================================//
// rd_data output assignment
//===========================================================================//
always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        // host_rd_en_reg <= 0;
        cgra_rd_en_reg <= 0;
        // cfg_rd_en_reg <= 0;
        // host_rd_data_reg <= 0;
        cgra_rd_data_reg <= 0;
        // cfg_rd_data_reg <= 0;
    end
    else begin
        // host_rd_en_reg <= host_rd_en;
        cgra_rd_en_reg <= cgra_rd_en;
        // cfg_rd_en_reg <= cfg_rd_en;
        // host_rd_data_reg <= host_rd_data;
        cgra_rd_data_reg <= cgra_rd_data;
        // cfg_rd_data_reg <= cfg_rd_data;
    end
end
// assign host_rd_data = host_rd_en_reg ? mem_data_out : host_rd_data_reg;
// assign cfg_rd_data = cfg_rd_en_reg ? mem_data_out : cfg_rd_data_reg;
assign cgra_rd_data = cgra_rd_en_reg ? mem_data_out : cgra_rd_data_reg;

endmodule
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
