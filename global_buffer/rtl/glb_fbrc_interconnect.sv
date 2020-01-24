/*=============================================================================
** Module: glb_fbrc_interconnect.sv
** Description:
**              Interconnect for fabric in global buffer
** Author: Taeyoung Kong
** Change history: 10/08/2019 - Implement first version
**===========================================================================*/
import global_buffer_pkg::*;

module glb_fbrc_interconnect (
    input  logic                            clk,
    input  logic                            clk_en,
    input  logic                            reset,
    input  logic [TILE_SEL_ADDR_WIDTH-1:0]  glb_tile_id,

    // start/done
    input  logic                            cgra_start_pulse,
    output logic                            cgra_done_pulse,

    // Config
    input  logic                            config_wr,
    input  logic                            config_rd,
    input  logic [GLB_CFG_REG_WIDTH-1:0]    config_addr,
    input  logic [CONFIG_DATA_WIDTH-1:0]    config_wr_data,
    output logic [CONFIG_DATA_WIDTH-1:0]    config_rd_data,
    
    // West
    input  logic                            f2b_wr_en_dwsti,
    input  logic [BANK_DATA_WIDTH-1:0]      f2b_wr_data_dwsti,
    input  logic [BANK_DATA_WIDTH-1:0]      f2b_wr_data_bit_sel_dwsti,
    input  logic                            f2b_rd_en_dwsti,
    input  logic [GLB_ADDR_WIDTH-1:0]       f2b_addr_dwsti,
    output logic [BANK_DATA_WIDTH-1:0]      b2f_rd_data_dwsto,
    output logic                            b2f_rd_data_valid_dwsto,

    // East
    output logic                            f2b_wr_en_desto,
    output logic [BANK_DATA_WIDTH-1:0]      f2b_wr_data_desto,
    output logic [BANK_DATA_WIDTH-1:0]      f2b_wr_data_bit_sel_desto,
    output logic                            f2b_rd_en_desto,
    output logic [GLB_ADDR_WIDTH-1:0]       f2b_addr_desto,
    input  logic [BANK_DATA_WIDTH-1:0]      b2f_rd_data_desti,
    input  logic                            b2f_rd_data_valid_desti,

    // South
    input  logic                            f2b_wr_en_sthi,
    input  logic [CGRA_DATA_WIDTH-1:0]      f2b_wr_word_sthi,
    input  logic                            f2b_rd_en_sthi,
    input  logic [CGRA_DATA_WIDTH-1:0]      f2b_addr_high_sthi,
    input  logic [CGRA_DATA_WIDTH-1:0]      f2b_addr_low_sthi,
    output logic [CGRA_DATA_WIDTH-1:0]      b2f_rd_word_stho,
    output logic                            b2f_rd_word_valid_stho,

    // Bank
    output logic                            f2b_wr_en [0:NUM_BANKS-1],
    output logic [BANK_DATA_WIDTH-1:0]      f2b_wr_data [0:NUM_BANKS-1],
    output logic [BANK_DATA_WIDTH-1:0]      f2b_wr_data_bit_sel [0:NUM_BANKS-1],
    output logic [BANK_ADDR_WIDTH-1:0]      f2b_wr_addr [0:NUM_BANKS-1],
    output logic                            f2b_rd_en [0:NUM_BANKS-1],
    output logic [BANK_ADDR_WIDTH-1:0]      f2b_rd_addr [0:NUM_BANKS-1],
    input  logic [BANK_DATA_WIDTH-1:0]      b2f_rd_data [0:NUM_BANKS-1]
);

//============================================================================//
// internal signals
//============================================================================//
logic [GLB_ADDR_WIDTH-1:0]      adgn_start_addr;
logic [GLB_ADDR_WIDTH-1:0]      adgn_num_words;
addr_gen_mode_t                 adgn_mode;
logic [NUM_BANKS-1:0]           adgn_switch_sel;
logic [CONFIG_DATA_WIDTH-1:0]   adgn_done_delay;

//============================================================================//
// configuration
//============================================================================//
always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        adgn_mode <= 0;
        adgn_start_addr <= 0;
        adgn_num_words <= 0;
        adgn_switch_sel <= 0;
        adgn_done_delay <= 0;
    end
    else begin
        if (config_wr) begin
            case (config_addr)
                0: adgn_mode <= config_wr_data[MODE_BIT_WIDTH-1:0];
                1: adgn_start_addr <= config_wr_data[GLB_ADDR_WIDTH-1:0];
                2: adgn_num_words <= config_wr_data[GLB_ADDR_WIDTH-1:0];
                3: adgn_switch_sel <= config_wr_data[NUM_BANKS-1:0];
                4: adgn_done_delay <= config_wr_data;
            endcase
        end
    end
end

always_comb begin
    config_rd_data = 0;
    if (config_rd) begin
        case (config_addr)
            0: config_rd_data = adgn_mode;
            1: config_rd_data = adgn_start_addr;
            2: config_rd_data = adgn_num_words;
            3: config_rd_data = adgn_switch_sel;
            4: config_rd_data = adgn_done_delay;
            default: config_rd_data = 0;
        endcase
    end
end

//============================================================================//
// cgra_start_pulse & cgra_done_pulse
//============================================================================//
logic cgra_done_pulse_int;
logic cgra_done_pulse_d1;

always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        cgra_done_pulse_d1 <= 0;
    end
    else begin
        cgra_done_pulse_d1 <= cgra_done_pulse_int;
    end
end
assign cgra_done_pulse = cgra_done_pulse_d1;

//============================================================================//
// address generator internal signal 
//============================================================================//
logic                           f2b_wr_en_adgno;
logic                           f2b_rd_en_adgno;
logic [BANK_DATA_WIDTH-1:0]     f2b_wr_data_adgno;
logic [BANK_DATA_WIDTH-1:0]     f2b_wr_data_bit_sel_adgno;
logic [GLB_ADDR_WIDTH-1:0]      f2b_addr_adgno;
logic [BANK_DATA_WIDTH-1:0]     b2f_rd_data_adgni;
logic                           b2f_rd_data_valid_adgni;

//============================================================================//
// glb fbrc address generator instantiation
//============================================================================//
glb_fbrc_address_generator glb_fbrc_address_generator_inst (
    .clk(clk),
    .clk_en(clk_en),
    .reset(reset),

    .cgra_start_pulse(cgra_start_pulse),
    .cgra_done_pulse(cgra_done_pulse_int),

    .start_addr(adgn_start_addr),
    .num_words(adgn_num_words),
    .mode(adgn_mode),
    .done_delay(adgn_done_delay),

    .cgra_to_io_wr_en(f2b_wr_en_sthi),
    .cgra_to_io_rd_en(f2b_rd_en_sthi),
    .cgra_to_io_addr_high(f2b_addr_high_sthi),
    .cgra_to_io_addr_low(f2b_addr_low_sthi),
    .cgra_to_io_wr_data(f2b_wr_word_sthi),
    .io_to_cgra_rd_data(b2f_rd_word_stho),
    .io_to_cgra_rd_data_valid(b2f_rd_word_valid_stho),

    .io_to_bank_wr_en(f2b_wr_en_adgno),
    .io_to_bank_wr_data(f2b_wr_data_adgno),
    .io_to_bank_wr_data_bit_sel(f2b_wr_data_bit_sel_adgno),
    .io_to_bank_rd_en(f2b_rd_en_adgno),
    .io_to_bank_addr(f2b_addr_adgno),
    .bank_to_io_rd_data(b2f_rd_data_adgni),
    .bank_to_io_rd_data_valid(b2f_rd_data_valid_adgni)
);

//============================================================================//
// cascade/bypass network 
//============================================================================//
logic                       int_f2b_wr_en [0:NUM_BANKS-1];
logic [BANK_DATA_WIDTH-1:0] int_f2b_wr_data [0:NUM_BANKS-1];
logic [BANK_DATA_WIDTH-1:0] int_f2b_wr_data_bit_sel [0:NUM_BANKS-1];
logic                       int_f2b_rd_en [0:NUM_BANKS-1];
logic [GLB_ADDR_WIDTH-1:0]  int_f2b_addr [0:NUM_BANKS-1];

always_comb begin
    for (int i=0; i<NUM_BANKS; i=i+1) begin
        if (i == 0) begin
            int_f2b_wr_en[0] = adgn_switch_sel[0] ? f2b_wr_en_adgno : f2b_wr_en_dwsti;
            int_f2b_wr_data[0] = adgn_switch_sel[0] ? f2b_wr_data_adgno : f2b_wr_data_dwsti;
            int_f2b_wr_data_bit_sel[0] = adgn_switch_sel[0] ? f2b_wr_data_bit_sel_adgno : f2b_wr_data_bit_sel_dwsti;
            int_f2b_addr[0] = adgn_switch_sel[0] ? f2b_addr_adgno : f2b_addr_dwsti;
            int_f2b_rd_en[0] = adgn_switch_sel[0] ? f2b_rd_en_adgno : f2b_rd_en_dwsti; 
        end
        else begin
            int_f2b_wr_en[i] = adgn_switch_sel[i] ? f2b_wr_en_adgno : int_f2b_wr_en[i-1];
            int_f2b_wr_data[i] = adgn_switch_sel[i] ? f2b_wr_data_adgno : int_f2b_wr_data[i-1];
            int_f2b_wr_data_bit_sel[i] = adgn_switch_sel[i] ? f2b_wr_data_bit_sel_adgno : int_f2b_wr_data_bit_sel[i-1];
            int_f2b_addr[i] = adgn_switch_sel[i] ? f2b_addr_adgno : int_f2b_addr[i-1];
            int_f2b_rd_en[i] = adgn_switch_sel[i] ? f2b_rd_en_adgno : int_f2b_rd_en[i-1];
        end
    end
end

// bypass
always_comb begin
    f2b_wr_en_desto = int_f2b_wr_en[NUM_BANKS-1];
    f2b_wr_data_desto = int_f2b_wr_data[NUM_BANKS-1];
    f2b_wr_data_bit_sel_desto = int_f2b_wr_data_bit_sel[NUM_BANKS-1];
    f2b_rd_en_desto = int_f2b_rd_en[NUM_BANKS-1];
    f2b_addr_desto = int_f2b_addr[NUM_BANKS-1];
end

//============================================================================//
// bank output assignment
//============================================================================//
logic int_addr_bank_en [0:NUM_BANKS-1];

always_comb begin
    for (int i=0; i<NUM_BANKS; i=i+1) begin
        int_addr_bank_en[i] = (int_f2b_addr[i][BANK_ADDR_WIDTH +: BANK_SEL_ADDR_WIDTH + TILE_SEL_ADDR_WIDTH] 
                               == ((glb_tile_id << BANK_SEL_ADDR_WIDTH) + i));
    end
end

always_comb begin
    for (int i=0; i<NUM_BANKS; i=i+1) begin
        f2b_wr_en[i] = int_f2b_wr_en[i] && int_addr_bank_en[i];
        f2b_wr_addr[i] = int_f2b_addr[i];
        f2b_wr_data[i] = int_f2b_wr_data[i];
        f2b_wr_data_bit_sel[i] = int_f2b_wr_data_bit_sel[i];
        f2b_rd_en[i] = int_f2b_rd_en[i] && int_addr_bank_en[i];
        f2b_rd_addr[i] = int_f2b_addr[i];
    end
end

//============================================================================//
// read data interconnection network with pipeline
//============================================================================//
logic [BANK_DATA_WIDTH-1:0] b2f_rd_data_d1 [0:NUM_BANKS-1];
logic [BANK_DATA_WIDTH-1:0] int_b2f_rd_data [0:NUM_BANKS-1];
logic                       int_b2f_rd_data_valid [0:NUM_BANKS-1];
logic                       f2b_rd_en_d1 [0:NUM_BANKS-1];
logic                       f2b_rd_en_d2 [0:NUM_BANKS-1];
logic                       b2f_rd_data_valid [0:NUM_BANKS-1];

assign b2f_rd_data_valid = f2b_rd_en_d2;

always_ff @(posedge clk) begin
    if (clk_en) begin
        for (int i=0; i<NUM_BANKS; i=i+1) begin
            f2b_rd_en_d1[i] <= f2b_rd_en[i];
            f2b_rd_en_d2[i] <= f2b_rd_en_d1[i];
        end
    end
end

always_ff @(posedge clk) begin
    if (clk_en) begin
        for (int i=0; i<NUM_BANKS; i=i+1) begin
            b2f_rd_data_d1[i] <= b2f_rd_data[i]; 
        end
    end
end

always_comb begin
    for (int i=NUM_BANKS-1; i>=0; i=i-1) begin
        if (i == NUM_BANKS-1) begin
            int_b2f_rd_data[NUM_BANKS-1] = f2b_rd_en_d2[NUM_BANKS-1] ? b2f_rd_data_d1[NUM_BANKS-1] : b2f_rd_data_desti;
            int_b2f_rd_data_valid[NUM_BANKS-1] = f2b_rd_en_d2[NUM_BANKS-1] ? b2f_rd_data_valid[NUM_BANKS-1] : b2f_rd_data_valid_desti;
        end
        else begin
            int_b2f_rd_data[i] = f2b_rd_en_d2[i] ? b2f_rd_data_d1[i] : int_b2f_rd_data[i+1];
            int_b2f_rd_data_valid[i] = f2b_rd_en_d2[i] ? b2f_rd_data_valid[i] : int_b2f_rd_data_valid[i+1];
        end
    end
end

always_comb begin
    for (int i=0; i<NUM_BANKS; i=i+1) begin
        if (adgn_switch_sel[i] == 1'b1) begin
            b2f_rd_data_adgni = int_b2f_rd_data[i];
            b2f_rd_data_valid_adgni = int_b2f_rd_data_valid[i];
        end
        else begin
            b2f_rd_data_adgni = 0;
            b2f_rd_data_valid_adgni = 0;
        end
    end
end

// read data bypass
always_comb begin
    b2f_rd_data_dwsto = int_b2f_rd_data[0];
    b2f_rd_data_valid_dwsto = int_b2f_rd_data_valid[0];
end

endmodule
