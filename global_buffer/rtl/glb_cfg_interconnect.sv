/*=============================================================================
** Module: glb_cfg_interconnect.sv
** Description:
**              Interconnect for configuration in global buffer
** Author: Taeyoung Kong
** Change history: 10/08/2019 - Implement first version
**===========================================================================*/
import global_buffer_pkg::*;

module glb_cfg_interconnect (
    input  logic                            clk,
    input  logic                            reset,
    input  logic [TILE_SEL_ADDR_WIDTH-1:0]  glb_tile_id,

    // start/done
    input  logic                            config_start_pulse,
    output logic                            config_done_pulse,

    // Config
    input  logic                            config_wr,
    input  logic                            config_rd,
    input  logic [GLB_CFG_REG_WIDTH-1:0]    config_addr,
    input  logic [CONFIG_DATA_WIDTH-1:0]    config_wr_data,
    output logic [CONFIG_DATA_WIDTH-1:0]    config_rd_data,
    
    // West
    input  logic                            c2b_rd_en_wsti,
    input  logic [GLB_ADDR_WIDTH-1:0]       c2b_addr_wsti,
    output logic [BANK_DATA_WIDTH-1:0]      b2c_rd_data_wsto,
    output logic                            b2c_rd_data_valid_wsto,

    // East
    output logic                            c2b_rd_en_esto,
    output logic [GLB_ADDR_WIDTH-1:0]       c2b_addr_esto,
    input  logic [BANK_DATA_WIDTH-1:0]      b2c_rd_data_esti,
    input  logic                            b2c_rd_data_valid_esti,

    // Bank
    output logic                            c2b_rd_en [0:NUM_BANKS-1],
    output logic [BANK_ADDR_WIDTH-1:0]      c2b_rd_addr [0:NUM_BANKS-1],
    input  logic [BANK_DATA_WIDTH-1:0]      b2c_rd_data [0:NUM_BANKS-1],

    // fbrc cfg
    output logic                            c2f_cfg_wr,
    output logic [CFG_ADDR_WIDTH-1:0]       c2f_cfg_addr,
    output logic [CFG_DATA_WIDTH-1:0]       c2f_cfg_data,

    // fbrc cfg west in
    input  logic                            c2f_cfg_wr_wsti,
    input  logic [CFG_ADDR_WIDTH-1:0]       c2f_cfg_addr_wsti,
    input  logic [CFG_DATA_WIDTH-1:0]       c2f_cfg_data_wsti,

    // fbrc cfg east out
    output logic                            c2f_cfg_wr_esto,
    output logic [CFG_ADDR_WIDTH-1:0]       c2f_cfg_addr_esto,
    output logic [CFG_DATA_WIDTH-1:0]       c2f_cfg_data_esto
);

//============================================================================//
// internal signals
//============================================================================//
logic [GLB_ADDR_WIDTH-1:0]      adgn_start_addr;
logic [GLB_ADDR_WIDTH-1:0]      adgn_num_words;
logic [NUM_BANKS-1:0]           adgn_switch_sel;

//============================================================================//
// configuration
//============================================================================//
always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        adgn_start_addr <= 0;
        adgn_num_words <= 0;
        adgn_switch_sel <= 0;
    end
    else begin
        if (config_wr) begin
            case (config_addr)
                0: adgn_start_addr <= config_wr_data[GLB_ADDR_WIDTH-1:0];
                1: adgn_num_words <= config_wr_data[GLB_ADDR_WIDTH-1:0];
                2: adgn_switch_sel <= config_wr_data[NUM_BANKS-1:0];
            endcase
        end
    end
end

always_comb begin
    config_rd_data = 0;
    if (config_rd) begin
        case (config_addr)
            0: config_rd_data = adgn_start_addr;
            1: config_rd_data = adgn_num_words;
            2: config_rd_data = adgn_switch_sel;
            default: config_rd_data = 0;
        endcase
    end
end

//============================================================================//
// config_start_pulse & config_done_pulse
//============================================================================//
logic config_done_pulse_int;
logic config_done_pulse_d1;

always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        config_done_pulse_d1 <= 0;
    end
    else begin
        config_done_pulse_d1 <= config_done_pulse_int;
    end
end
assign config_done_pulse = config_done_pulse_d1;

//============================================================================//
// address generator internal signal 
//============================================================================//
logic                           c2b_rd_en_adgno;
logic [GLB_ADDR_WIDTH-1:0]      c2b_addr_adgno;
logic [BANK_DATA_WIDTH-1:0]     b2c_rd_data_adgni;
logic                           b2c_rd_data_valid_adgni;

logic                           c2f_cfg_wr_adgno;
logic [CFG_ADDR_WIDTH-1:0]      c2f_cfg_addr_adgno;
logic [CFG_DATA_WIDTH-1:0]      c2f_cfg_data_adgno;

//============================================================================//
// glb fbrc address generator instantiation
//============================================================================//
glb_cfg_address_generator glb_cfg_address_generator_inst (
    .clk(clk),
    .reset(reset),

    .config_start_pulse(config_start_pulse),
    .config_done_pulse(config_done_pulse_int),

    .start_addr(adgn_start_addr),
    .num_words(adgn_num_words),

    .cfg_to_cgra_config_wr(c2f_cfg_wr_adgno),
    .cfg_to_cgra_config_addr(c2f_cfg_addr_adgno),
    .cfg_to_cgra_config_data(c2f_cfg_data_adgno),

    .cfg_to_bank_rd_en(c2b_rd_en_adgno),
    .cfg_to_bank_addr(c2b_addr_adgno),
    .bank_to_cfg_rd_data(b2c_rd_data_adgni),
    .bank_to_cfg_rd_data_valid(b2c_rd_data_valid_adgni)
);

//============================================================================//
// cascade/bypass network 
//============================================================================//
logic                       int_c2b_rd_en [0:NUM_BANKS-1];
logic [GLB_ADDR_WIDTH-1:0]  int_c2b_addr [0:NUM_BANKS-1];

always_comb begin
    for (int i=0; i<NUM_BANKS; i=i+1) begin
        if (i == 0) begin
            int_c2b_addr[0] = adgn_switch_sel[0] ? c2b_addr_adgno : c2b_addr_wsti;
            int_c2b_rd_en[0] = adgn_switch_sel[0] ? c2b_rd_en_adgno : c2b_rd_en_wsti; 
        end
        else begin
            int_c2b_addr[i] = adgn_switch_sel[i] ? c2b_addr_adgno : int_c2b_addr[i-1];
            int_c2b_rd_en[i] = adgn_switch_sel[i] ? c2b_rd_en_adgno : int_c2b_rd_en[i-1];
        end
    end
end

// bypass
always_comb begin
    c2b_rd_en_esto = int_c2b_rd_en[NUM_BANKS-1];
    c2b_addr_esto = int_c2b_addr[NUM_BANKS-1];
end

//============================================================================//
// bank output assignment
//============================================================================//
logic int_addr_bank_en [0:NUM_BANKS-1];

always_comb begin
    for (int i=0; i<NUM_BANKS; i=i+1) begin
        int_addr_bank_en[i] = (int_c2b_addr[i][BANK_ADDR_WIDTH +: BANK_SEL_ADDR_WIDTH + TILE_SEL_ADDR_WIDTH] 
                               == ((glb_tile_id << BANK_SEL_ADDR_WIDTH) + i));
    end
end

always_comb begin
    for (int i=0; i<NUM_BANKS; i=i+1) begin
        c2b_rd_en[i] = int_c2b_rd_en[i] && int_addr_bank_en[i];
        c2b_rd_addr[i] = int_c2b_addr[i];
    end
end

//============================================================================//
// read data interconnection network with pipeline
//============================================================================//
logic [BANK_DATA_WIDTH-1:0] b2c_rd_data_d1 [0:NUM_BANKS-1];
logic [BANK_DATA_WIDTH-1:0] int_b2c_rd_data [0:NUM_BANKS-1];
logic                       int_b2c_rd_data_valid [0:NUM_BANKS-1];
logic                       c2b_rd_en_d1 [0:NUM_BANKS-1];
logic                       c2b_rd_en_d2 [0:NUM_BANKS-1];
logic                       b2c_rd_data_valid [0:NUM_BANKS-1];

assign b2c_rd_data_valid = c2b_rd_en_d2;

always_ff @(posedge clk) begin
    for (int i=0; i<NUM_BANKS; i=i+1) begin
        c2b_rd_en_d1[i] <= c2b_rd_en[i];
        c2b_rd_en_d2[i] <= c2b_rd_en_d1[i];
    end
end

always_ff @(posedge clk) begin
    for (int i=0; i<NUM_BANKS; i=i+1) begin
        b2c_rd_data_d1[i] <= b2c_rd_data[i]; 
    end
end

always_comb begin
    for (int i=NUM_BANKS-1; i>=0; i=i-1) begin
        if (i == NUM_BANKS-1) begin
            int_b2c_rd_data[NUM_BANKS-1] = c2b_rd_en_d2[NUM_BANKS-1] ? b2c_rd_data_d1[NUM_BANKS-1] : b2c_rd_data_esti;
            int_b2c_rd_data_valid[NUM_BANKS-1] = c2b_rd_en_d2[NUM_BANKS-1] ? b2c_rd_data_valid[NUM_BANKS-1] : b2c_rd_data_valid_esti;
        end
        else begin
            int_b2c_rd_data[i] = c2b_rd_en_d2[i] ? b2c_rd_data_d1[i] : int_b2c_rd_data[i+1];
            int_b2c_rd_data_valid[i] = c2b_rd_en_d2[i] ? b2c_rd_data_valid[i] : int_b2c_rd_data_valid[i+1];
        end
    end
end

always_comb begin
    for (int i=0; i<NUM_BANKS; i=i+1) begin
        if (adgn_switch_sel[i] == 1'b1) begin
            b2c_rd_data_adgni = int_b2c_rd_data[i];
            b2c_rd_data_valid_adgni = int_b2c_rd_data_valid[i];
        end
        else begin
            b2c_rd_data_adgni = 0;
            b2c_rd_data_valid_adgni = 0;
        end
    end
end

// read data bypass
always_comb begin
    b2c_rd_data_wsto = int_b2c_rd_data[0];
    b2c_rd_data_valid_wsto = int_b2c_rd_data_valid[0];
end

//============================================================================//
// Bitstream assign
//============================================================================//
// if address generator is turned off, just use the previous cfg from west
always_comb begin
    if (adgn_switch_sel == {NUM_BANKS{1'b0}}) begin
        c2f_cfg_wr = c2f_cfg_wr_wsti;
        c2f_cfg_addr = c2f_cfg_addr_wsti; 
        c2f_cfg_data = c2f_cfg_data_wsti;
    end
    else begin
        c2f_cfg_wr = c2f_cfg_wr_adgno;
        c2f_cfg_addr = c2f_cfg_addr_adgno; 
        c2f_cfg_data = c2f_cfg_data_adgno;
    end
end

endmodule
