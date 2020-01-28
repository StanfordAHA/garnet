/*=============================================================================
** Module: global_buffer.sv
** Description:
**              Global Buffer
** Author: Taeyoung Kong
** Change history: 10/08/2019 - Implement first version of global buffer
**===========================================================================*/

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

    output logic                            glb_to_cgra_cfg_wr [0:NUM_TILES-1],
    output logic                            glb_to_cgra_cfg_rd [0:NUM_TILES-1],
    output logic [CFG_ADDR_WIDTH-1:0]       glb_to_cgra_cfg_addr [0:NUM_TILES-1],
    output logic [CFG_DATA_WIDTH-1:0]       glb_to_cgra_cfg_data [0:NUM_TILES-1],

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
logic [TILE_SEL_ADDR_WIDTH-1:0] int_glb_tile_id [0:NUM_TILES-1];
logic [CONFIG_DATA_WIDTH-1:0]   int_glb_config_rd_data [0:NUM_TILES-1];
logic [CONFIG_DATA_WIDTH-1:0]   int_glb_sram_config_rd_data [0:NUM_TILES-1];
logic                           int_cgra_done_pulse [0:NUM_TILES-1];
logic                           int_config_done_pulse [0:NUM_TILES-1];

// East - host
logic                           int_h2b_wr_en_desti [0:NUM_TILES-1];
logic [BANK_DATA_WIDTH/8-1:0]   int_h2b_wr_strb_desti [0:NUM_TILES-1];
logic [GLB_ADDR_WIDTH-1:0]      int_h2b_wr_addr_desti [0:NUM_TILES-1];
logic [BANK_DATA_WIDTH-1:0]     int_h2b_wr_data_desti [0:NUM_TILES-1];
logic                           int_h2b_rd_en_desti [0:NUM_TILES-1];
logic [GLB_ADDR_WIDTH-1:0]      int_h2b_rd_addr_desti [0:NUM_TILES-1];
logic [BANK_DATA_WIDTH-1:0]     int_b2h_rd_data_desto [0:NUM_TILES-1];

// West - host
logic                           int_h2b_wr_en_dwsto [0:NUM_TILES-1];
logic [BANK_DATA_WIDTH/8-1:0]   int_h2b_wr_strb_dwsto [0:NUM_TILES-1];
logic [GLB_ADDR_WIDTH-1:0]      int_h2b_wr_addr_dwsto [0:NUM_TILES-1];
logic [BANK_DATA_WIDTH-1:0]     int_h2b_wr_data_dwsto [0:NUM_TILES-1];
logic                           int_h2b_rd_en_dwsto [0:NUM_TILES-1];
logic [GLB_ADDR_WIDTH-1:0]      int_h2b_rd_addr_dwsto [0:NUM_TILES-1];
logic [BANK_DATA_WIDTH-1:0]     int_b2h_rd_data_dwsti [0:NUM_TILES-1];

// West - fbrc
logic                           int_f2b_wr_en_dwsti [0:NUM_TILES-1];
logic [BANK_DATA_WIDTH-1:0]     int_f2b_wr_data_dwsti [0:NUM_TILES-1];
logic [BANK_DATA_WIDTH-1:0]     int_f2b_wr_data_bit_sel_dwsti [0:NUM_TILES-1];
logic                           int_f2b_rd_en_dwsti [0:NUM_TILES-1];
logic [GLB_ADDR_WIDTH-1:0]      int_f2b_addr_dwsti [0:NUM_TILES-1];
logic [BANK_DATA_WIDTH-1:0]     int_b2f_rd_data_dwsto [0:NUM_TILES-1];
logic                           int_b2f_rd_data_valid_dwsto [0:NUM_TILES-1];

// East - fbrc
logic                           int_f2b_wr_en_desto [0:NUM_TILES-1];
logic [BANK_DATA_WIDTH-1:0]     int_f2b_wr_data_desto [0:NUM_TILES-1];
logic [BANK_DATA_WIDTH-1:0]     int_f2b_wr_data_bit_sel_desto [0:NUM_TILES-1];
logic                           int_f2b_rd_en_desto [0:NUM_TILES-1];
logic [GLB_ADDR_WIDTH-1:0]      int_f2b_addr_desto [0:NUM_TILES-1];
logic [BANK_DATA_WIDTH-1:0]     int_b2f_rd_data_desti [0:NUM_TILES-1];
logic                           int_b2f_rd_data_valid_desti [0:NUM_TILES-1];

// South - fbrc
logic                           int_f2b_wr_en_sthi [0:NUM_TILES-1];
logic [CGRA_DATA_WIDTH-1:0]     int_f2b_wr_word_sthi [0:NUM_TILES-1];
logic                           int_f2b_rd_en_sthi [0:NUM_TILES-1];
logic [CGRA_DATA_WIDTH-1:0]     int_f2b_addr_high_sthi [0:NUM_TILES-1];
logic [CGRA_DATA_WIDTH-1:0]     int_f2b_addr_low_sthi [0:NUM_TILES-1];
logic [CGRA_DATA_WIDTH-1:0]     int_b2f_rd_word_stho [0:NUM_TILES-1];
logic                           int_b2f_rd_word_valid_stho [0:NUM_TILES-1];

// West - cfg-bank
logic                           int_c2b_rd_en_dwsti [0:NUM_TILES-1];
logic [GLB_ADDR_WIDTH-1:0]      int_c2b_addr_dwsti [0:NUM_TILES-1];
logic [BANK_DATA_WIDTH-1:0]     int_b2c_rd_data_dwsto [0:NUM_TILES-1];
logic                           int_b2c_rd_data_valid_dwsto [0:NUM_TILES-1];

// East - cfg-bank
logic                           int_c2b_rd_en_desto [0:NUM_TILES-1];
logic [GLB_ADDR_WIDTH-1:0]      int_c2b_addr_desto [0:NUM_TILES-1];
logic [BANK_DATA_WIDTH-1:0]     int_b2c_rd_data_desti [0:NUM_TILES-1];
logic                           int_b2c_rd_data_valid_desti [0:NUM_TILES-1];

// West - cfg
logic                           int_c2f_cfg_wr_dwsti [0:NUM_TILES-1];
logic [CFG_ADDR_WIDTH-1:0]      int_c2f_cfg_addr_dwsti [0:NUM_TILES-1];
logic [CFG_DATA_WIDTH-1:0]      int_c2f_cfg_data_dwsti [0:NUM_TILES-1];

// East - cfg
logic                           int_c2f_cfg_wr_desto [0:NUM_TILES-1];
logic [CFG_ADDR_WIDTH-1:0]      int_c2f_cfg_addr_desto [0:NUM_TILES-1];
logic [CFG_DATA_WIDTH-1:0]      int_c2f_cfg_data_desto [0:NUM_TILES-1];

// South - cfg
logic                           int_c2f_cfg_wr [0:NUM_TILES-1];
logic [CFG_ADDR_WIDTH-1:0]      int_c2f_cfg_addr [0:NUM_TILES-1];
logic [CFG_DATA_WIDTH-1:0]      int_c2f_cfg_data [0:NUM_TILES-1];

//============================================================================//
// internal signal connection
//============================================================================//
// clk_en
assign clk_en = !glc_to_io_stall;

// glb_tile_id
always_comb begin
    for (int i=0; i<NUM_TILES; i=i+1) begin
        int_glb_tile_id[i] = i;
    end
end

// cgra_done_pulse interrupt
always_comb begin
    cgra_done_pulse = '0;
    for (int i=0; i<NUM_TILES; i=i+1) begin
        cgra_done_pulse = cgra_done_pulse | int_cgra_done_pulse[i];
    end
end

// config_done_pulse interrupt
always_comb begin
    config_done_pulse = '0;
    for (int i=0; i<NUM_TILES; i=i+1) begin
        config_done_pulse = config_done_pulse | int_config_done_pulse[i];
    end
end

// bitstream read
always_comb begin
    for (int i=0; i<NUM_TILES; i=i+1) begin
        glb_to_cgra_cfg_rd[i] = glc_to_cgra_cfg_rd;
    end
end

// bitstream write
always_comb begin
    for (int i=0; i<NUM_TILES; i=i+1) begin
        glb_to_cgra_cfg_wr[i] = int_c2f_cfg_wr[i] | glc_to_cgra_cfg_wr;
    end
end

// bitstream addr
always_comb begin
    if (glc_to_cgra_cfg_rd | glc_to_cgra_cfg_wr) begin
        for (int i=0; i<NUM_TILES; i=i+1) begin
            glb_to_cgra_cfg_addr[i] = glc_to_cgra_cfg_addr;
        end
    end
    else begin
        for (int i=0; i<NUM_TILES; i=i+1) begin
            glb_to_cgra_cfg_addr[i] = int_c2f_cfg_addr[i];
        end
    end
end

// bitstream data
always_comb begin
    if (glc_to_cgra_cfg_rd | glc_to_cgra_cfg_wr) begin
        for (int i=0; i<NUM_TILES; i=i+1) begin
            glb_to_cgra_cfg_data[i] = glc_to_cgra_cfg_data;
        end
    end
    else begin
        for (int i=0; i<NUM_TILES; i=i+1) begin
            glb_to_cgra_cfg_data[i] = int_c2f_cfg_data[i];
        end
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
            int_h2b_wr_en_desti[NUM_TILES-1] = |host_to_glb_wr_strb;
            int_h2b_wr_strb_desti[NUM_TILES-1] = host_to_glb_wr_strb;
            int_h2b_wr_addr_desti[NUM_TILES-1] = host_to_glb_wr_addr;
            int_h2b_wr_data_desti[NUM_TILES-1] = host_to_glb_wr_data;
            int_h2b_rd_en_desti[NUM_TILES-1] = host_to_glb_rd_en;
            int_h2b_rd_addr_desti[NUM_TILES-1] = host_to_glb_rd_addr;
        end
        else begin
            int_h2b_wr_en_desti[i] = int_h2b_wr_en_dwsto[i+1];
            int_h2b_wr_strb_desti[i] = int_h2b_wr_strb_dwsto[i+1]; 
            int_h2b_wr_addr_desti[i] = int_h2b_wr_addr_dwsto[i+1]; 
            int_h2b_wr_data_desti[i] = int_h2b_wr_data_dwsto[i+1]; 
            int_h2b_rd_en_desti[i] = int_h2b_rd_en_dwsto[i+1];
            int_h2b_rd_addr_desti[i] = int_h2b_rd_addr_dwsto[i+1]; 
        end
    end
end

// host - west to east connection
always_comb begin
    for (int i=0; i<NUM_TILES; i=i+1) begin
        if (i==0) begin
            int_b2h_rd_data_dwsti[0] = '0;
        end
        else begin
            int_b2h_rd_data_dwsti[i] = int_b2h_rd_data_desto[i-1];
        end
    end
end
assign glb_to_host_rd_data = int_b2h_rd_data_desto[NUM_TILES-1]; 

// fbrc - east-west connection
always_comb begin
    for (int i=NUM_TILES-1; i>=0; i=i-1) begin
        if (i==(NUM_TILES-1)) begin
            int_b2f_rd_data_desti[NUM_TILES-1] = '0;
            int_b2f_rd_data_valid_desti[NUM_TILES-1] = '0;
        end
        else begin
            int_b2f_rd_data_desti[i] = int_b2f_rd_data_dwsto[i+1];
            int_b2f_rd_data_valid_desti[i] = int_b2f_rd_data_valid_dwsto[i+1];
        end
    end
end

// fbrc - west to east connection
always_comb begin
    for (int i=0; i<NUM_TILES; i=i+1) begin
        if (i==0) begin
            int_f2b_wr_en_dwsti[0] = '0;
            int_f2b_wr_data_dwsti[0] = '0;
            int_f2b_wr_data_bit_sel_dwsti[0] = '0;
            int_f2b_rd_en_dwsti[0] = '0;
            int_f2b_addr_dwsti[0] = '0;
        end
        else begin
            int_f2b_wr_en_dwsti[i] = int_f2b_wr_en_desto[i-1];
            int_f2b_wr_data_dwsti[i] = int_f2b_wr_data_desto[i-1];
            int_f2b_wr_data_bit_sel_dwsti[i] = int_f2b_wr_data_bit_sel_desto[i-1];
            int_f2b_rd_en_dwsti[i] = int_f2b_rd_en_desto[i-1];
            int_f2b_addr_dwsti[i] = int_f2b_addr_desto[i-1];
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

// cfg-bank - east-west connection
always_comb begin
    for (int i=NUM_TILES-1; i>=0; i=i-1) begin
        if (i==(NUM_TILES-1)) begin
            int_b2c_rd_data_desti[NUM_TILES-1] = '0;
            int_b2c_rd_data_valid_desti[NUM_TILES-1] = '0;
        end
        else begin
            int_b2c_rd_data_desti[i] = int_b2c_rd_data_dwsto[i+1];
            int_b2c_rd_data_valid_desti[i] = int_b2c_rd_data_valid_dwsto[i+1];
        end
    end
end

// cfg-bank - west to east connection
always_comb begin
    for (int i=0; i<NUM_TILES; i=i+1) begin
        if (i==0) begin
            int_c2b_rd_en_dwsti[0] = '0;
            int_c2b_addr_dwsti[0] = '0;
        end
        else begin
            int_c2b_rd_en_dwsti[i] = int_c2b_rd_en_desto[i-1];
            int_c2b_addr_dwsti[i] = int_c2b_addr_desto[i-1];
        end
    end
end

// cfg-fbrc - west to east connection
always_comb begin
    for (int i=0; i<NUM_TILES; i=i+1) begin
        if (i==0) begin
            int_c2f_cfg_wr_dwsti[0] = '0;
            int_c2f_cfg_addr_dwsti[0] = '0;
            int_c2f_cfg_data_dwsti[0] = '0;
        end
        else begin
            int_c2f_cfg_wr_dwsti[i] = int_c2f_cfg_wr_desto[i-1];
            int_c2f_cfg_addr_dwsti[i] = int_c2f_cfg_addr_desto[i-1];
            int_c2f_cfg_data_dwsti[i] = int_c2f_cfg_data_desto[i-1];
        end
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
        .glb_tile_id(int_glb_tile_id[i]),

        .cgra_start_pulse(cgra_start_pulse),
        .cgra_done_pulse(int_cgra_done_pulse[i]),

        .config_start_pulse(config_start_pulse),
        .config_done_pulse(int_config_done_pulse[i]),
        
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

        .h2b_wr_en_desti(int_h2b_wr_en_desti[i]),
        .h2b_wr_strb_desti(int_h2b_wr_strb_desti[i]),
        .h2b_wr_addr_desti(int_h2b_wr_addr_desti[i]),
        .h2b_wr_data_desti(int_h2b_wr_data_desti[i]),
        .h2b_rd_en_desti(int_h2b_rd_en_desti[i]),
        .h2b_rd_addr_desti(int_h2b_rd_addr_desti[i]),
        .b2h_rd_data_desto(int_b2h_rd_data_desto[i]),

        .h2b_wr_en_dwsto(int_h2b_wr_en_dwsto[i]),
        .h2b_wr_strb_dwsto(int_h2b_wr_strb_dwsto[i]),
        .h2b_wr_addr_dwsto(int_h2b_wr_addr_dwsto[i]),
        .h2b_wr_data_dwsto(int_h2b_wr_data_dwsto[i]),
        .h2b_rd_en_dwsto(int_h2b_rd_en_dwsto[i]),
        .h2b_rd_addr_dwsto(int_h2b_rd_addr_dwsto[i]),
        .b2h_rd_data_dwsti(int_b2h_rd_data_dwsti[i]),

        .f2b_wr_en_dwsti(int_f2b_wr_en_dwsti[i]),
        .f2b_wr_data_dwsti(int_f2b_wr_data_dwsti[i]),
        .f2b_wr_data_bit_sel_dwsti(int_f2b_wr_data_bit_sel_dwsti[i]),
        .f2b_rd_en_dwsti(int_f2b_rd_en_dwsti[i]),
        .f2b_addr_dwsti(int_f2b_addr_dwsti[i]),
        .b2f_rd_data_dwsto(int_b2f_rd_data_dwsto[i]),
        .b2f_rd_data_valid_dwsto(int_b2f_rd_data_valid_dwsto[i]),

        .f2b_wr_en_desto(int_f2b_wr_en_desto[i]),
        .f2b_wr_data_desto(int_f2b_wr_data_desto[i]),
        .f2b_wr_data_bit_sel_desto(int_f2b_wr_data_bit_sel_desto[i]),
        .f2b_rd_en_desto(int_f2b_rd_en_desto[i]),
        .f2b_addr_desto(int_f2b_addr_desto[i]),
        .b2f_rd_data_desti(int_b2f_rd_data_desti[i]),
        .b2f_rd_data_valid_desti(int_b2f_rd_data_valid_desti[i]),

        .f2b_wr_en_sthi(int_f2b_wr_en_sthi[i]),
        .f2b_wr_word_sthi(int_f2b_wr_word_sthi[i]),
        .f2b_rd_en_sthi(int_f2b_rd_en_sthi[i]),
        .f2b_addr_high_sthi(int_f2b_addr_high_sthi[i]),
        .f2b_addr_low_sthi(int_f2b_addr_low_sthi[i]),
        .b2f_rd_word_stho(int_b2f_rd_word_stho[i]),
        .b2f_rd_word_valid_stho(int_b2f_rd_word_valid_stho[i]),

        .c2b_rd_en_dwsti(int_c2b_rd_en_dwsti[i]),
        .c2b_addr_dwsti(int_c2b_addr_dwsti[i]),
        .b2c_rd_data_dwsto(int_b2c_rd_data_dwsto[i]),
        .b2c_rd_data_valid_dwsto(int_b2c_rd_data_valid_dwsto[i]),

        .c2b_rd_en_desto(int_c2b_rd_en_desto[i]),
        .c2b_addr_desto(int_c2b_addr_desto[i]),
        .b2c_rd_data_desti(int_b2c_rd_data_desti[i]),
        .b2c_rd_data_valid_desti(int_b2c_rd_data_valid_desti[i]),

        .c2f_cfg_wr_dwsti(int_c2f_cfg_wr_dwsti[i]),
        .c2f_cfg_addr_dwsti(int_c2f_cfg_addr_dwsti[i]),
        .c2f_cfg_data_dwsti(int_c2f_cfg_data_dwsti[i]),

        .c2f_cfg_wr_desto(int_c2f_cfg_wr_desto[i]),
        .c2f_cfg_addr_desto(int_c2f_cfg_addr_desto[i]),
        .c2f_cfg_data_desto(int_c2f_cfg_data_desto[i]),

        .c2f_cfg_wr(int_c2f_cfg_wr[i]),
        .c2f_cfg_addr(int_c2f_cfg_addr[i]),
        .c2f_cfg_data(int_c2f_cfg_data[i])
    );
end: generate_tile
endgenerate

endmodule
