/*=============================================================================
** Module: glb_tile_cfg.sv
** Description:
**              Global Buffer Tile Configuration Registers
** Author: Taeyoung Kong
** Change history: 02/06/2020 - Implement first version
**===========================================================================*/
import global_buffer_pkg::*;

module glb_tile_cfg (
    input  logic                            clk,
    input  logic                            reset,
    input  logic [TILE_SEL_ADDR_WIDTH-1:0]  glb_tile_id,

    // Config
    cfg_ifc.slave                           if_cfg_est_s,
    cfg_ifc.master                          if_cfg_wst_m,
    input  logic                            cfg_wr_clk_en,
    input  logic                            cfg_rd_clk_en,

    // Config Register
    output logic [TILE_SEL_ADDR_WIDTH-1:0]  cfg_multi_tile_size,
    output logic                            cfg_tile_is_start,
    output logic                            cfg_tile_is_end,
    output logic                            cfg_store_dma_on,
    output logic                            cfg_store_dma_auto_on,
    output dma_st_header_t                  cfg_store_dma_header [QUEUE_DEPTH],
    input  logic                            cfg_store_dma_invalidate_pulse [QUEUE_DEPTH]
);

//============================================================================//
// Configuration registers
//============================================================================//
logic [3:0] cfg_wr_addr_tile_int;
logic [4:0] cfg_wr_addr_reg_int;

logic [3:0] cfg_rd_addr_tile_int;
logic [4:0] cfg_rd_addr_reg_int;

assign cfg_wr_addr_tile_int = if_cfg_est_s.wr_addr[10:7];
assign cfg_wr_addr_reg_int = if_cfg_est_s.wr_addr[6:2];

assign cfg_rd_addr_tile_int = if_cfg_est_s.rd_addr[10:7];
assign cfg_rd_addr_reg_int = if_cfg_est_s.rd_addr[6:2];

logic cfg_wr_tile_id_match;
logic cfg_rd_tile_id_match;
assign cfg_wr_tile_id_match = (if_cfg_est_s.wr_en && (glb_tile_id == cfg_wr_addr_tile_int)) ? 1'b1 : 1'b0;
assign cfg_rd_tile_id_match = (if_cfg_est_s.rd_en && (glb_tile_id == cfg_rd_addr_tile_int)) ? 1'b1 : 1'b0;

logic [AXI_DATA_WIDTH-1:0] cfg_rd_data_int;

always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        cfg_multi_tile_size <= '0;
        cfg_tile_is_start <= 0;
        cfg_tile_is_end <= 0;

        cfg_store_dma_on <= 0;
        cfg_store_dma_auto_on <= 0;

        for (int i=0; i<QUEUE_DEPTH; i=i+1) begin
            cfg_store_dma_header[i] <= '0;
        end
    end
    else if (cfg_wr_clk_en) begin
        if (cfg_wr_tile_id_match) begin
            case (cfg_wr_addr_reg_int)
                0: {cfg_tile_is_end, cfg_tile_is_start, cfg_multi_tile_size} <= if_cfg_est_s.wr_data[TILE_SEL_ADDR_WIDTH+1:0];
                1: {cfg_store_dma_auto_on, cfg_store_dma_on} <= if_cfg_est_s.wr_data[1:0];
                2: cfg_store_dma_header[0].num_words <= if_cfg_est_s.wr_data[MAX_NUM_WORDS_WIDTH-1:0];
                3: {cfg_store_dma_header[0].start_addr, cfg_store_dma_header[0].valid} <= if_cfg_est_s.wr_data[GLB_ADDR_WIDTH:0];
                4: cfg_store_dma_header[1].num_words <= if_cfg_est_s.wr_data[MAX_NUM_WORDS_WIDTH-1:0];
                5: {cfg_store_dma_header[1].start_addr, cfg_store_dma_header[1].valid} <= if_cfg_est_s.wr_data[GLB_ADDR_WIDTH:0];
                6: cfg_store_dma_header[2].num_words <= if_cfg_est_s.wr_data[MAX_NUM_WORDS_WIDTH-1:0];
                7: {cfg_store_dma_header[2].start_addr, cfg_store_dma_header[2].valid} <= if_cfg_est_s.wr_data[GLB_ADDR_WIDTH:0];
                8: cfg_store_dma_header[3].num_words <= if_cfg_est_s.wr_data[MAX_NUM_WORDS_WIDTH-1:0];
                9: {cfg_store_dma_header[3].start_addr, cfg_store_dma_header[3].valid} <= if_cfg_est_s.wr_data[GLB_ADDR_WIDTH:0];
            endcase
        end
        else begin
            for (int i=0; i<QUEUE_DEPTH; i=i+1) begin
                if (cfg_store_dma_invalidate_pulse[i] == 1'b1) begin
                    cfg_store_dma_header[i].valid <= 0;
                end
            end
        end
    end
end

always_comb begin
    cfg_rd_data_int = '0;
    if (cfg_rd_tile_id_match) begin
        case (cfg_rd_addr_reg_int)
            0: cfg_rd_data_int = {cfg_tile_is_end, cfg_tile_is_start, cfg_multi_tile_size};
            1: cfg_rd_data_int = {cfg_store_dma_auto_on, cfg_store_dma_on};
            2: cfg_rd_data_int = cfg_store_dma_header[0].num_words;
            3: cfg_rd_data_int = {cfg_store_dma_header[0].start_addr, cfg_store_dma_header[0].valid};
            4: cfg_rd_data_int = cfg_store_dma_header[1].num_words;
            5: cfg_rd_data_int = {cfg_store_dma_header[1].start_addr, cfg_store_dma_header[1].valid};
            6: cfg_rd_data_int = cfg_store_dma_header[2].num_words;
            7: cfg_rd_data_int = {cfg_store_dma_header[2].start_addr, cfg_store_dma_header[2].valid};
            8: cfg_rd_data_int = cfg_store_dma_header[3].num_words;
            9: cfg_rd_data_int = {cfg_store_dma_header[3].start_addr, cfg_store_dma_header[3].valid};
            default: cfg_rd_data_int = '0;
        endcase
    end
    else begin
        cfg_rd_data_int = '0;
    end
end

//============================================================================//
// Configuration Router
//============================================================================//
// east to west - wr
always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        if_cfg_wst_m.wr_en <= '0;
        if_cfg_wst_m.wr_addr <= '0;
        if_cfg_wst_m.wr_data <= '0;
    end
    else if (cfg_wr_clk_en)  begin
        if (if_cfg_est_s.wr_en == 1'b1 && !cfg_wr_tile_id_match) begin
            if_cfg_wst_m.wr_en <= if_cfg_est_s.wr_en;
            if_cfg_wst_m.wr_addr <= if_cfg_est_s.wr_addr;
            if_cfg_wst_m.wr_data <= if_cfg_est_s.wr_data;
        end
        else begin
            if_cfg_wst_m.wr_en <= 0;
            if_cfg_wst_m.wr_addr <= '0;
            if_cfg_wst_m.wr_data <= '0;
        end
    end
end

// east to west - rd
always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        if_cfg_wst_m.rd_en <= '0;
        if_cfg_wst_m.rd_addr <= '0;
    end
    else if (cfg_rd_clk_en)  begin
        if (if_cfg_est_s.rd_en == 1'b1 && !cfg_rd_tile_id_match) begin
            if_cfg_wst_m.rd_en <= if_cfg_est_s.rd_en;
            if_cfg_wst_m.rd_addr <= if_cfg_est_s.rd_addr;
        end
        else begin
            if_cfg_wst_m.rd_en <= 0;
            if_cfg_wst_m.rd_addr <= '0;
        end
    end
end

// west to east
always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        if_cfg_est_s.rd_data <= '0;
        if_cfg_est_s.rd_data_valid <= 0;
    end
    else if (cfg_rd_clk_en) begin
        if (cfg_rd_tile_id_match) begin
            if_cfg_est_s.rd_data <= cfg_rd_data_int;
            if_cfg_est_s.rd_data_valid <= 1;
        end
        else begin
            if_cfg_est_s.rd_data <= if_cfg_wst_m.rd_data;
            if_cfg_est_s.rd_data_valid <= if_cfg_wst_m.rd_data_valid;
        end
    end
end

endmodule
