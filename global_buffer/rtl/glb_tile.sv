/*=============================================================================
** Module: glb_tile.sv
** Description:
**              Global Buffer Tile
** Author: Taeyoung Kong
** Change history: 01/08/2020 - Implement first version of global buffer tile
**===========================================================================*/
import global_buffer_pkg::*;

module glb_tile (
    input  logic                            clk,
    input  logic                            clk_en,
    input  logic                            reset,
    input  logic [TILE_SEL_ADDR_WIDTH-1:0]  glb_tile_id,

    // Config
    cfg_ifc.slave                           if_cfg_est_s,
    cfg_ifc.master                          if_cfg_wst_m,

    // Glb SRAM Config

    // write packet
    input  wr_packet_t                      wr_packet_wsti,
    output wr_packet_t                      wr_packet_wsto,
    input  wr_packet_t                      wr_packet_esti,
    output wr_packet_t                      wr_packet_esto,

    // cgra streaming word
    input  logic [CGRA_DATA_WIDTH-1:0]      stream_data_f2g,
    input  logic                            stream_data_valid_f2g,

    input  logic [2*NUM_TILES-1:0]          interrupt_pulse_wsti,
    output logic [2*NUM_TILES-1:0]          interrupt_pulse_esto

    // TODO
    // output logic [CGRA_DATA_WIDTH-1:0]      stream_out_data_stho,
    // output logic                            stream_out_data_valid_stho,

    // configuration
    // TODO
    // output logic                            g2c_cfg_wr,
    // output logic [CGRA_CFG_ADDR_WIDTH-1:0]  g2c_cfg_addr,
    // output logic [CGRA_CFG_DATA_WIDTH-1:0]  g2c_cfg_data
);

//============================================================================//
// Internal Logic
//============================================================================//
wr_packet_t wr_packet_r2c; // router to core
wr_packet_t wr_packet_c2r; // core to router

logic                   stream_in_done_pulse;
logic [2*NUM_TILES-1:0] interrupt_pulse_esto_int;
logic [2*NUM_TILES-1:0] interrupt_pulse_esto_int_d1;

//============================================================================//
// Configuration registers
//============================================================================//
logic           cfg_tile_is_start;
logic           cfg_tile_is_end;
logic           cfg_store_dma_on;
logic           cfg_store_dma_auto_on;
dma_header_t    cfg_store_dma_header [QUEUE_DEPTH];

logic [3:0] cfg_wr_addr_tile_int;
logic [4:0] cfg_wr_addr_reg_int;
logic [4:0] cfg_wr_addr_store_dma_int;
logic [4:0] cfg_wr_addr_load_dma_int;

logic [3:0] cfg_rd_addr_tile_int;
logic [4:0] cfg_rd_addr_reg_int;
logic [4:0] cfg_rd_addr_store_dma_int;
logic [4:0] cfg_rd_addr_load_dma_int;

assign cfg_wr_addr_tile_int = if_cfg_est_s.wr_addr[10:7];
assign cfg_wr_addr_reg_int = if_cfg_est_s.wr_addr[6:2];
assign cfg_wr_addr_store_dma_int = cfg_wr_addr_reg_int - 2;
assign cfg_wr_addr_load_dma_int = cfg_wr_addr_store_dma_int - 2 * QUEUE_DEPTH;

assign cfg_rd_addr_tile_int = if_cfg_est_s.rd_addr[10:7];
assign cfg_rd_addr_reg_int = if_cfg_est_s.rd_addr[6:2];
assign cfg_rd_addr_store_dma_int = cfg_rd_addr_reg_int - 2;
assign cfg_rd_addr_load_dma_int = cfg_rd_addr_store_dma_int - 2 * QUEUE_DEPTH;

logic cfg_wr_tile_id_match;
logic cfg_rd_tile_id_match;
assign cfg_wr_tile_id_match = (glb_tile_id == cfg_wr_addr_tile_int) ? 1'b1 : 1'b0;
assign cfg_rd_tile_id_match = (glb_tile_id == cfg_rd_addr_tile_int) ? 1'b1 : 1'b0;

logic cfg_wr_en_int;
logic cfg_wr_addr_int;
logic cfg_wr_data_int;
logic cfg_rd_en_int;
logic cfg_rd_addr_int;
logic cfg_rd_data_int;

always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        cfg_tile_is_start <= 0;
        cfg_tile_is_end <= 0;

        cfg_store_dma_on <= 0;
        cfg_store_dma_auto_on <= 0;

        for (int i=0; i<QUEUE_DEPTH; i=i+1) begin
            cfg_store_dma_header[i] <= '0;
        end
    end
    else begin
        if (if_cfg_est_s.wr_en && cfg_wr_tile_id_match) begin
            if (cfg_wr_addr_reg_int == 'd0) begin
                {cfg_tile_is_end, cfg_tile_is_start} <= if_cfg_est_s.wr_data[1:0];
            end
            else if (cfg_wr_addr_reg_int == 'd1) begin
                {cfg_store_dma_auto_on, cfg_store_dma_on} <= if_cfg_est_s.wr_data[1:0];
            end
            // else if (cfg_wr_addr_reg_int == 'd2) begin
            //     {cfg_load_dma_auto_on, cfg_load_dma_on} <= if_cfg_est_s.wr_data[1:0];
            // end
            else if ((cfg_wr_addr_reg_int - 2) < 2 * QUEUE_DEPTH) begin // store dma
                if (cfg_wr_addr_store_dma_int[0] == 0) begin
                    {cfg_store_dma_header[cfg_wr_addr_store_dma_int[2:1]].start_addr, 
                     cfg_store_dma_header[cfg_wr_addr_store_dma_int[2:1]].valid} <= if_cfg_est_s.wr_data[GLB_ADDR_WIDTH:0];
                end
                else begin
                    cfg_store_dma_header[cfg_wr_addr_store_dma_int[2:1]].num_words <= if_cfg_est_s.wr_data[MAX_NUM_WORDS_WIDTH-1:0];
                end
            end
            // else if ((cfg_wr_addr_reg_int - 2)  // load dma
            //     end
            // end
        end
    end
end

always_comb begin
    cfg_rd_data_int = '0;
    if (if_cfg_est_s.rd_en && cfg_rd_tile_id_match) begin
        if (cfg_rd_addr_reg_int == 'd0) begin
            cfg_rd_data_int = {cfg_tile_is_end, cfg_tile_is_start};
        end
        else if (cfg_rd_addr_reg_int == 'd1) begin
            cfg_rd_data_int = {cfg_store_dma_auto_on, cfg_store_dma_on};
        end
        // else if (cfg_rd_addr_reg_int == 'd2) begin
        //     cfg_rd_data_int = {cfg_load_dma_auto_on, cfg_load_dma_on};
        // end
        else if ((cfg_rd_addr_reg_int - 2) < 2 * QUEUE_DEPTH) begin // store dma
            if (cfg_rd_addr_store_dma_int[0] == 0) begin
                cfg_rd_data_int = {cfg_store_dma_header[cfg_wr_addr_store_dma_int[2:1]].start_addr, 
                                   cfg_store_dma_header[cfg_wr_addr_store_dma_int[2:1]].valid};
            end
            else begin
                cfg_rd_data_int = cfg_store_dma_header[cfg_wr_addr_store_dma_int[2:1]].num_words;
            end
        end
        // load dma
        else begin
            cfg_rd_data_int = '0;
        end
    end
end

//============================================================================//
// Configuration Router
//============================================================================//
// east to west
always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        if_cfg_wst_m.wr_en <= '0;
        if_cfg_wst_m.wr_addr <= '0;
        if_cfg_wst_m.wr_data <= '0;
        if_cfg_wst_m.rd_en <= '0;
        if_cfg_wst_m.rd_addr <= '0;
    end
    else begin
        if (if_cfg_est_s.wr_en == 1'b1 && !cfg_wr_tile_id_match) begin
            if_cfg_wst_m.wr_en <= if_cfg_est_s.wr_en;
            if_cfg_wst_m.wr_addr <= if_cfg_est_s.wr_addr;
            if_cfg_wst_m.wr_data <= if_cfg_est_s.wr_data;
        end
        if (if_cfg_est_s.rd_en == 1'b1 && !cfg_rd_tile_id_match) begin
            if_cfg_wst_m.rd_en <= if_cfg_est_s.rd_en;
            if_cfg_wst_m.rd_addr <= if_cfg_est_s.rd_addr;
        end
    end
end

// west to east
always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        if_cfg_est_s.rd_data <= '0;
        if_cfg_est_s.rd_data_valid <= 0;
    end
    else begin
        if (if_cfg_est_s.rd_en == 1'b1 && cfg_rd_tile_id_match) begin
            if_cfg_est_s.rd_data <= cfg_rd_data_int;
            if_cfg_est_s.rd_data_valid <= 1;
        end
        else if (if_cfg_wst_m.rd_data_valid == 1'b1) begin
            if_cfg_est_s.rd_data <= if_cfg_wst_m.rd_data;
            if_cfg_est_s.rd_data_valid <= 1;
        end
    end
end

//============================================================================//
// Interrupt pulse
//============================================================================//
always_comb begin
    interrupt_pulse_esto_int = interrupt_pulse_wsti;
    interrupt_pulse_esto_int[2 * glb_tile_id] = stream_in_done_pulse;
    // interrupt_pulse_esto[2 * glb_tile_id + 1] = stream_out_done_pulse;
end

always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        interrupt_pulse_esto_int_d1 <= '0;
    end
    else if (clk_en) begin
        interrupt_pulse_esto_int_d1 <= interrupt_pulse_esto_int;
    end
end
assign interrupt_pulse_esto = interrupt_pulse_esto_int_d1;

//============================================================================//
// Global Buffer Core
//============================================================================//
glb_core glb_core (.*);

//============================================================================//
// Router
//============================================================================//
glb_tile_router glb_tile_router (.*);

endmodule
