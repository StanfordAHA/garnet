/*=============================================================================
** Module: glb_tile_cfg_ctrl.sv
** Description:
**              Global Buffer Tile Config and Pio Interface
** Author: Taeyoung Kong
** Change history: 04/05/2020
**  - Implement first version of control logic
**===========================================================================*/
import global_buffer_pkg::*;
import global_buffer_param::*;

module glb_tile_cfg_ctrl #(
    parameter REG_ADDR_WIDTH = 6
) (
    input  logic                            clk,
    input  logic                            reset,
    input  logic [TILE_SEL_ADDR_WIDTH-1:0]  glb_tile_id,

    // Config
    cfg_ifc.slave                           if_cfg_wst_s,
    cfg_ifc.master                          if_cfg_est_m,

    output logic [AXI_DATA_WIDTH-1:0]       h2d_pio_dec_write_data,
    output logic [REG_ADDR_WIDTH-1:0]       h2d_pio_dec_address,
    output logic                            h2d_pio_dec_read,
    output logic                            h2d_pio_dec_write,

    input  logic [AXI_DATA_WIDTH-1:0]       d2h_dec_pio_read_data,
    input  logic                            d2h_dec_pio_ack,
    input  logic                            d2h_dec_pio_nack
);

//============================================================================//
// Internal logic defines
//============================================================================//
logic [AXI_DATA_WIDTH-1:0] wr_data_internal;
logic [REG_ADDR_WIDTH-1:0] addr_internal;
logic read_internal;
logic write_internal;
logic rd_en_d1, rd_en_d2;
logic [AXI_DATA_WIDTH-1:0] rd_data_internal, rd_data_next;
logic rd_data_valid_internal, rd_data_valid_next;
logic wr_tile_id_match;
logic rd_tile_id_match;

//============================================================================//
// assigns
//============================================================================//
assign h2d_pio_dec_write_data = wr_data_internal;
assign h2d_pio_dec_address = addr_internal;
assign h2d_pio_dec_read = read_internal;
assign h2d_pio_dec_write = write_internal;

//============================================================================//
// combinational logic
//============================================================================//
always_comb begin
    wr_tile_id_match = (glb_tile_id == if_cfg_wst_s.wr_addr[(REG_ADDR_WIDTH+AXI_BYTE_OFFSET) +: TILE_SEL_ADDR_WIDTH]);
    rd_tile_id_match = (glb_tile_id == if_cfg_wst_s.rd_addr[(REG_ADDR_WIDTH+AXI_BYTE_OFFSET) +: TILE_SEL_ADDR_WIDTH]);
end

always_comb begin
    wr_data_internal = '0;
    addr_internal = '0;
    read_internal = 0;
    write_internal = 0;
    // write address override read address when both are asserted
    if (if_cfg_wst_s.rd_en & rd_tile_id_match) begin
        addr_internal = if_cfg_wst_s.rd_addr[AXI_BYTE_OFFSET +: REG_ADDR_WIDTH];
        read_internal = 1;
    end
    if (if_cfg_wst_s.wr_en & wr_tile_id_match) begin
        wr_data_internal = if_cfg_wst_s.wr_data;
        addr_internal = if_cfg_wst_s.wr_addr[AXI_BYTE_OFFSET +: REG_ADDR_WIDTH];
        write_internal = 1;
    end
end

//============================================================================//
// control logic
//============================================================================//
always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        rd_en_d1 <= 0;
        rd_en_d2 <= 0;
    end
    else begin
        rd_en_d1 <= read_internal;
        rd_en_d2 <= rd_en_d1;
    end
end

always_comb begin
    rd_data_valid_next = 0;
    rd_data_next = '0;
    if (rd_en_d2 & (d2h_dec_pio_ack | d2h_dec_pio_nack)) begin
        rd_data_valid_next = 1;
        rd_data_next = d2h_dec_pio_read_data;
    end
end

always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        rd_data_valid_internal <= 0;
        rd_data_internal <= '0;
    end
    else begin
        rd_data_valid_internal <= rd_data_valid_next;
        rd_data_internal <= rd_data_next;
    end
end

//============================================================================//
// Configuration Router and Pipeline
//============================================================================//
// west to east - wr
always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        if_cfg_est_m.wr_en <= 0;
        if_cfg_est_m.wr_addr <= '0;
        if_cfg_est_m.wr_data <= '0;
    end
    else if (if_cfg_wst_s.wr_en == 1'b1 && !wr_tile_id_match) begin
        if_cfg_est_m.wr_en <= if_cfg_wst_s.wr_en;
        if_cfg_est_m.wr_addr <= if_cfg_wst_s.wr_addr;
        if_cfg_est_m.wr_data <= if_cfg_wst_s.wr_data;
    end
    else begin
        if_cfg_est_m.wr_en <= 0;
        if_cfg_est_m.wr_addr <= '0;
        if_cfg_est_m.wr_data <= '0;
    end
    // end
    // else begin
    //     if_cfg_est_m.wr_en <= 0;
    //     if_cfg_est_m.wr_addr <= '0;
    //     if_cfg_est_m.wr_data <= '0;
    // end
end
// always_ff @(negedge clk or posedge reset) begin
//     if (reset) begin
//         if_cfg_est_m.wr_clk_en <= 0;
//     end
//     else begin
//         if_cfg_est_m.wr_clk_en <= if_cfg_wst_s.wr_clk_en;
//     end
// end
// west to east - rd
always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        if_cfg_est_m.rd_en <= 0;
        if_cfg_est_m.rd_addr <= '0;
    end
    else if (if_cfg_wst_s.rd_en == 1'b1 && !rd_tile_id_match) begin
        if_cfg_est_m.rd_en <= if_cfg_wst_s.rd_en;
        if_cfg_est_m.rd_addr <= if_cfg_wst_s.rd_addr;
    end
    else begin
        if_cfg_est_m.rd_en <= 0;
        if_cfg_est_m.rd_addr <= '0;
    end
    // end
    // else begin
    //     if_cfg_est_m.rd_en <= 0;
    //     if_cfg_est_m.rd_addr <= '0;
    // end
end

// always_ff @(negedge clk or posedge reset) begin
//     if (reset) begin
//         if_cfg_est_m.rd_clk_en <= 0;
//     end
//     else begin
//         if_cfg_est_m.rd_clk_en <= if_cfg_wst_s.rd_clk_en;
//     end
// end

// east to west
always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        if_cfg_wst_s.rd_data <= '0;
        if_cfg_wst_s.rd_data_valid <= 0;
    end
    else begin
        if (rd_data_valid_internal) begin
            if_cfg_wst_s.rd_data <= rd_data_internal;
            if_cfg_wst_s.rd_data_valid <= rd_data_valid_internal;
        end
        else begin
            if_cfg_wst_s.rd_data <= if_cfg_est_m.rd_data;
            if_cfg_wst_s.rd_data_valid <= if_cfg_est_m.rd_data_valid;
        end
    end
end

assign if_cfg_est_m.wr_clk_en = 1;
assign if_cfg_est_m.rd_clk_en = 1;

endmodule
