/*=============================================================================
** Module: global_buffer.sv
** Description:
**              Global Buffer
** Author: Taeyoung Kong
** Change history: 10/08/2019 - Implement first version of global buffer
**===========================================================================*/
`include "global_buffer_pkg.sv"

import global_buffer_pkg::*;

module global_buffer (
    input  logic                            clk,
    input  logic                            reset,

    input  logic [BANK_DATA_WIDTH/8-1:0]    host_to_glb_wr_strb,
    input  logic [GLB_ADDR_WIDTH-1:0]       host_to_glb_wr_addr,
    input  logic [BANK_DATA_WIDTH-1:0]      host_to_glb_wr_data,
    input  logic                            host_to_glb_rd_en,
    input  logic [GLB_ADDR_WIDTH-1:0]       host_to_glb_rd_addr,
    output logic [BANK_DATA_WIDTH-1:0]      glb_to_host_rd_data,

    input  logic                            cgra_to_glb_wr_en [0:NUM_TILES-1],
    input  logic                            cgra_to_glb_rd_en [0:NUM_TILES-1],
    input  logic [CGRA_DATA_WIDTH-1:0]      cgra_to_glb_wr_data [0:NUM_TILES-1],
    input  logic [CGRA_DATA_WIDTH-1:0]      cgra_to_glb_addr_high [0:NUM_TILES-1],
    input  logic [CGRA_DATA_WIDTH-1:0]      cgra_to_glb_addr_low [0:NUM_TILES-1],
    output logic [CGRA_DATA_WIDTH-1:0]      glb_to_cgra_rd_data [0:NUM_TILES-1],
    output logic                            glb_to_cgra_rd_data_valid [0:NUM_TILES-1],

    input  logic                            glc_to_cgra_cfg_wr,
    input  logic                            glc_to_cgra_cfg_rd,
    input  logic [CFG_ADDR_WIDTH-1:0]       glc_to_cgra_cfg_addr,
    input  logic [CFG_DATA_WIDTH-1:0]       glc_to_cgra_cfg_data,

    output logic                            glb_to_cgra_cfg_wr [NUM_TILES-1:0],
    output logic                            glb_to_cgra_cfg_rd [NUM_TILES-1:0],
    output logic [CFG_ADDR_WIDTH-1:0]       glb_to_cgra_cfg_addr [NUM_TILES-1:0],
    output logic [CFG_DATA_WIDTH-1:0]       glb_to_cgra_cfg_data [NUM_TILES-1:0],

    input  logic                            glc_to_io_stall,
    input  logic                            cgra_start_pulse,
    output logic                            cgra_done_pulse,
    input  logic                            config_start_pulse,
    output logic                            config_done_pulse,

    input  logic                            glb_config_wr,
    input  logic                            glb_config_rd,
    input  logic [GLB_CFG_ADDR_WIDTH-1:0]   glb_config_addr,
    input  logic [CFG_DATA_WIDTH-1:0]       glb_config_wr_data,
    output logic [CFG_DATA_WIDTH-1:0]       glb_config_rd_data,

    input  logic                            glb_sram_config_wr,
    input  logic                            glb_sram_config_rd,
    input  logic [CFG_ADDR_WIDTH-1:0]       glb_sram_config_addr,
    input  logic [CFG_DATA_WIDTH-1:0]       glb_sram_config_wr_data,
    output logic [CFG_DATA_WIDTH-1:0]       glb_sram_config_rd_data
);

//============================================================================//
// internal signal declaration
//============================================================================//
// control
logic                           clk_en;

// config
logic [TILE_SEL_ADDR_WIDTH-1:0] int_glb_tile_col [0:NUM_TILES-1];
logic [CONFIG_DATA_WIDTH-1:0]   int_glb_config_rd_data [0:NUM_TILES-1];
logic [CONFIG_DATA_WIDTH-1:0]   int_glb_sram_config_rd_data [0:NUM_TILES-1];
logic                           int_cgra_done [0:NUM_TILES-1];
logic                           cgra_done;
logic                           cgra_done_d1;
logic                           cgra_done_pulse;

// East - host
logic                           int_h2b_wr_en_esti [0:NUM_TILES-1];
logic [BANK_DATA_WIDTH/8-1:0]   int_h2b_wr_strb_esti [0:NUM_TILES-1];
logic [GLB_ADDR_WIDTH-1:0]      int_h2b_wr_addr_esti [0:NUM_TILES-1];
logic [BANK_DATA_WIDTH-1:0]     int_h2b_wr_data_esti [0:NUM_TILES-1];
logic                           int_h2b_rd_en_esti [0:NUM_TILES-1];
logic [GLB_ADDR_WIDTH-1:0]      int_h2b_rd_addr_esti [0:NUM_TILES-1];
logic [BANK_DATA_WIDTH-1:0]     int_b2h_rd_data_esto [0:NUM_TILES-1];

// West - host
logic                           int_h2b_wr_en_wsto [0:NUM_TILES-1];
logic [BANK_DATA_WIDTH/8-1:0]   int_h2b_wr_strb_wsto [0:NUM_TILES-1];
logic [GLB_ADDR_WIDTH-1:0]      int_h2b_wr_addr_wsto [0:NUM_TILES-1];
logic [BANK_DATA_WIDTH-1:0]     int_h2b_wr_data_wsto [0:NUM_TILES-1];
logic                           int_h2b_rd_en_wsto [0:NUM_TILES-1];
logic [GLB_ADDR_WIDTH-1:0]      int_h2b_rd_addr_wsto [0:NUM_TILES-1];
logic [BANK_DATA_WIDTH-1:0]     int_b2h_rd_data_wsti [0:NUM_TILES-1];

// West - fbrc
logic                           int_f2b_wr_en_wsti [0:NUM_TILES-1];
logic [BANK_DATA_WIDTH-1:0]     int_f2b_wr_data_wsti [0:NUM_TILES-1];
logic [BANK_DATA_WIDTH-1:0]     int_f2b_wr_data_bit_sel_wsti [0:NUM_TILES-1];
logic                           int_f2b_rd_en_wsti [0:NUM_TILES-1];
logic [GLB_ADDR_WIDTH-1:0]      int_f2b_addr_wsti [0:NUM_TILES-1];
logic [BANK_DATA_WIDTH-1:0]     int_b2f_rd_data_wsto [0:NUM_TILES-1];
logic                           int_b2f_rd_data_valid_wsto [0:NUM_TILES-1];

// East - fbrc
logic                           int_f2b_wr_en_esto [0:NUM_TILES-1];
logic [BANK_DATA_WIDTH-1:0]     int_f2b_wr_data_esto [0:NUM_TILES-1];
logic [BANK_DATA_WIDTH-1:0]     int_f2b_wr_data_bit_sel_esto [0:NUM_TILES-1];
logic                           int_f2b_rd_en_esto [0:NUM_TILES-1];
logic [GLB_ADDR_WIDTH-1:0]      int_f2b_addr_esto [0:NUM_TILES-1];
logic [BANK_DATA_WIDTH-1:0]     int_b2f_rd_data_esti [0:NUM_TILES-1];
logic                           int_b2f_rd_data_valid_esti [0:NUM_TILES-1];

// South - fbrc
logic                           int_f2b_wr_en_sthi [0:NUM_TILES-1];
logic [CGRA_DATA_WIDTH-1:0]     int_f2b_wr_word_sthi [0:NUM_TILES-1];
logic                           int_f2b_rd_en_sthi [0:NUM_TILES-1];
logic [CGRA_DATA_WIDTH-1:0]     int_f2b_addr_high_sthi [0:NUM_TILES-1];
logic [CGRA_DATA_WIDTH-1:0]     int_f2b_addr_low_sthi [0:NUM_TILES-1];
logic [CGRA_DATA_WIDTH-1:0]     int_b2f_rd_word_stho [0:NUM_TILES-1];
logic                           int_b2f_rd_word_valid_stho [0:NUM_TILES-1];

//============================================================================//
// internal signal connection
//============================================================================//
// clk_en
assign clk_en = !glc_to_io_stall;

// glb_tile_col
always_comb begin
    for (int i=0; i<NUM_TILES; i=i+1) begin
        int_glb_tile_col[i] = i;
    end
end

// cgra_done
always_comb begin
    cgra_done = '1;
    for (int i=0; i<NUM_TILES; i=i+1) begin
        cgra_done = cgra_done & int_cgra_done[i];
    end
end
// generate pulse for one cycle
always_ff @(posedge clk) begin
    cgra_done_d1 <= cgra_done;
end
assign cgra_done_pulse = cgra_done & (!cgra_done_d1);
assign config_done_pulse = '0;

// bypass parallel configuration for now
always_comb begin
    for (int i=0; i<NUM_TILES; i=i+1) begin
        glb_to_cgra_cfg_wr[i] = glc_to_cgra_cfg_wr;
        glb_to_cgra_cfg_rd[i] = glc_to_cgra_cfg_rd;
        glb_to_cgra_cfg_addr[i] = glc_to_cgra_cfg_addr;
        glb_to_cgra_cfg_data[i] = glc_to_cgra_cfg_data;
    end
end

// glb_config_rd_data
always_comb begin
    glb_config_rd_data = '0;
    for (int i=0; i<NUM_TILES; i=i+1) begin
        glb_config_rd_data = glb_config_rd_data | int_glb_config_rd_data[i];
    end
end

// glb_sram_config_rd_data
always_comb begin
    glb_sram_config_rd_data = '0;
    for (int i=0; i<NUM_TILES; i=i+1) begin
        glb_sram_config_rd_data = glb_sram_config_rd_data | int_glb_sram_config_rd_data[i];
    end
end

// host - east to west connection
always_comb begin
    for (int i=NUM_TILES-1; i>=0; i=i-1) begin
        if (i==(NUM_TILES-1)) begin
            int_h2b_wr_en_esti[NUM_TILES-1] = |host_to_glb_wr_strb;
            int_h2b_wr_strb_esti[NUM_TILES-1] = host_to_glb_wr_strb;
            int_h2b_wr_addr_esti[NUM_TILES-1] = host_to_glb_wr_addr;
            int_h2b_wr_data_esti[NUM_TILES-1] = host_to_glb_wr_data;
            int_h2b_rd_en_esti[NUM_TILES-1] = host_to_glb_rd_en;
            int_h2b_rd_addr_esti[NUM_TILES-1] = host_to_glb_rd_addr;
        end
        else begin
            int_h2b_wr_en_esti[i] = int_h2b_wr_en_wsto[i+1];
            int_h2b_wr_strb_esti[i] = int_h2b_wr_strb_wsto[i+1]; 
            int_h2b_wr_addr_esti[i] = int_h2b_wr_addr_wsto[i+1]; 
            int_h2b_wr_data_esti[i] = int_h2b_wr_data_wsto[i+1]; 
            int_h2b_rd_en_esti[i] = int_h2b_rd_en_wsto[i+1];
            int_h2b_rd_addr_esti[i] = int_h2b_rd_addr_wsto[i+1]; 
        end
    end
end

// host - west to east connection
always_comb begin
    for (int i=0; i<NUM_TILES; i=i+1) begin
        if (i==0) begin
            int_b2h_rd_data_wsti[0] = '0;
        end
        else begin
            int_b2h_rd_data_wsti[i] = int_b2h_rd_data_esto[i-1];
        end
    end
end
assign glb_to_host_rd_data = int_b2h_rd_data_esto[NUM_TILES-1]; 

// fbrc - east-west connection
always_comb begin
    for (int i=NUM_TILES-1; i>=0; i=i-1) begin
        if (i==(NUM_TILES-1)) begin
            int_b2f_rd_data_esti[NUM_TILES-1] = '0;
            int_b2f_rd_data_valid_esti[NUM_TILES-1] = '0;
        end
        else begin
            int_b2f_rd_data_esti[i] = int_b2f_rd_data_wsto[i+1];
            int_b2f_rd_data_valid_esti[i] = int_b2f_rd_data_valid_wsto[i+1];
        end
    end
end

// fbrc - west to east connection
always_comb begin
    for (int i=0; i<NUM_TILES; i=i+1) begin
        if (i==0) begin
            int_f2b_wr_en_wsti[0] = '0;
            int_f2b_wr_data_wsti[0] = '0;
            int_f2b_wr_data_bit_sel_wsti[0] = '0;
            int_f2b_rd_en_wsti[0] = '0;
            int_f2b_addr_wsti[0] = '0;
        end
        else begin
            int_f2b_wr_en_wsti[i] = int_f2b_wr_en_esto[i-1];
            int_f2b_wr_data_wsti[i] = int_f2b_wr_data_esto[i-1];
            int_f2b_wr_data_bit_sel_wsti[i] = int_f2b_wr_data_bit_sel_esto[i-1];
            int_f2b_rd_en_wsti[i] = int_f2b_rd_en_esto[i-1];
            int_f2b_addr_wsti[i] = int_f2b_addr_esto[i-1];
        end
    end
end

// fbrc - cgra to south connection
always_comb begin
    for (int i=0; i<NUM_TILES; i=i+1) begin
        int_f2b_wr_en_sthi[i] = cgra_to_glb_wr_en[i];
        int_f2b_wr_word_sthi[i] = cgra_to_glb_wr_data[i];
        int_f2b_rd_en_sthi[i] = cgra_to_glb_rd_en[i];
        int_f2b_addr_high_sthi[i] = cgra_to_glb_addr_high[i];
        int_f2b_addr_low_sthi[i] = cgra_to_glb_addr_low[i];
    end
end

// fbrc - south to cgra connection
always_comb begin
    for (int i=0; i<NUM_TILES; i=i+1) begin
        glb_to_cgra_rd_data[i] = int_b2f_rd_word_stho[i];
        glb_to_cgra_rd_data_valid[i] = int_b2f_rd_word_valid_stho[i];
    end
end

//============================================================================//
// glb_tile array instantiation
//============================================================================//
genvar i;
generate
for (i = 0; i < NUM_TILES; i=i+1) begin: generate_tile
    glb_tile glb_tile_inst (
        .clk(clk),
        .clk_en(clk_en),
        .reset(reset),
        .glb_tile_col(int_glb_tile_col[i]),

        .cgra_start_pulse(cgra_start_pulse),
        .cgra_done(int_cgra_done[i]),
        
        .glb_config_wr(glb_config_wr),
        .glb_config_rd(glb_config_rd),
        .glb_config_addr(glb_config_addr),
        .glb_config_wr_data(glb_config_wr_data),
        .glb_config_rd_data(int_glb_config_rd_data[i]),
        
        .glb_sram_config_wr(glb_sram_config_wr),
        .glb_sram_config_rd(glb_sram_config_rd),
        .glb_sram_config_addr(glb_sram_config_addr),
        .glb_sram_config_wr_data(glb_sram_config_wr_data),
        .glb_sram_config_rd_data(int_glb_sram_config_rd_data[i]),

        .h2b_wr_en_esti(int_h2b_wr_en_esti[i]),
        .h2b_wr_strb_esti(int_h2b_wr_strb_esti[i]),
        .h2b_wr_addr_esti(int_h2b_wr_addr_esti[i]),
        .h2b_wr_data_esti(int_h2b_wr_data_esti[i]),
        .h2b_rd_en_esti(int_h2b_rd_en_esti[i]),
        .h2b_rd_addr_esti(int_h2b_rd_addr_esti[i]),
        .b2h_rd_data_esto(int_b2h_rd_data_esto[i]),

        .h2b_wr_en_wsto(int_h2b_wr_en_wsto[i]),
        .h2b_wr_strb_wsto(int_h2b_wr_strb_wsto[i]),
        .h2b_wr_addr_wsto(int_h2b_wr_addr_wsto[i]),
        .h2b_wr_data_wsto(int_h2b_wr_data_wsto[i]),
        .h2b_rd_en_wsto(int_h2b_rd_en_wsto[i]),
        .h2b_rd_addr_wsto(int_h2b_rd_addr_wsto[i]),
        .b2h_rd_data_wsti(int_b2h_rd_data_wsti[i]),

        .f2b_wr_en_wsti(int_f2b_wr_en_wsti[i]),
        .f2b_wr_data_wsti(int_f2b_wr_data_wsti[i]),
        .f2b_wr_data_bit_sel_wsti(int_f2b_wr_data_bit_sel_wsti[i]),
        .f2b_rd_en_wsti(int_f2b_rd_en_wsti[i]),
        .f2b_addr_wsti(int_f2b_addr_wsti[i]),
        .b2f_rd_data_wsto(int_b2f_rd_data_wsto[i]),
        .b2f_rd_data_valid_wsto(int_b2f_rd_data_valid_wsto[i]),

        .f2b_wr_en_esto(int_f2b_wr_en_esto[i]),
        .f2b_wr_data_esto(int_f2b_wr_data_esto[i]),
        .f2b_wr_data_bit_sel_esto(int_f2b_wr_data_bit_sel_esto[i]),
        .f2b_rd_en_esto(int_f2b_rd_en_esto[i]),
        .f2b_addr_esto(int_f2b_addr_esto[i]),
        .b2f_rd_data_esti(int_b2f_rd_data_esti[i]),
        .b2f_rd_data_valid_esti(int_b2f_rd_data_valid_esti[i]),

        .f2b_wr_en_sthi(int_f2b_wr_en_sthi[i]),
        .f2b_wr_word_sthi(int_f2b_wr_word_sthi[i]),
        .f2b_rd_en_sthi(int_f2b_rd_en_sthi[i]),
        .f2b_addr_high_sthi(int_f2b_addr_high_sthi[i]),
        .f2b_addr_low_sthi(int_f2b_addr_low_sthi[i]),
        .b2f_rd_word_stho(int_b2f_rd_word_stho[i]),
        .b2f_rd_word_valid_stho(int_b2f_rd_word_valid_stho[i])
    );
end: generate_tile
endgenerate

endmodule
