/*=============================================================================
** Module: glb_tile_dummy_axil_s_ctrl.sv
** Description:
**              axi-lite slave controller
** Author: Taeyoung Kong
** Change history: 02/01/2020 - Finish hand-written axi-lite slave controller
**===========================================================================*/
`include "axil_ifc.sv"
`include "cfg_ifc.sv"
import global_buffer_pkg::*;

module glb_tile_dummy_axil_s_ctrl (
    input  logic    clk,
    input  logic    reset,

    output logic    cfg_wr_tile_clk_en,
    output logic    cfg_rd_tile_clk_en,
    output logic    cfg_wr_interrupt_clk_en,
    output logic    cfg_rd_interrupt_clk_en,

    axil_ifc.slave  if_axil,
    cfg_ifc.master  if_cfg_tile,
    cfg_ifc.master  if_cfg_interrupt
);

//============================================================================//
// Enum states
//============================================================================//
typedef enum logic[2:0] {
    RD_IDLE = 3'h0,
    RD_REQ_INTERRUPT = 3'h1,
    RD_REQ_TILE = 3'h2,
    RD_WAIT = 3'h3,
    RD_RESP = 3'h4
} RdState;
RdState rd_state;

typedef enum logic[2:0] {
    WR_IDLE = 3'h0,
    WR_REQ_INTERRUPT = 3'h1,
    WR_REQ_TILE = 3'h2,
    WR_WAIT = 3'h3,
    WR_RESP = 3'h4
} WrState;
WrState wr_state;

//============================================================================//
// internal wires
//============================================================================//
logic [$clog2(NUM_TILES):0] wr_wait_cnt;
logic cfg_rd_is_tile;

logic cfg_wr_tile_clk_en_p;
logic cfg_rd_tile_clk_en_p;
logic cfg_wr_interrupt_clk_en_p;
logic cfg_rd_interrupt_clk_en_p;

//============================================================================//
// write FSM
//============================================================================//
always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        wr_state <= WR_IDLE;
        cfg_wr_tile_clk_en_p <= 0;
        cfg_wr_interrupt_clk_en_p <= 0;

        // axi interface
        if_axil.awready <= '1;
        if_axil.wready <= '1;
        if_axil.bresp <= 2'b00;
        if_axil.bvalid <= '0;

        // interrupt cfg interface
        if_cfg_interrupt.wr_en <= '0;
        if_cfg_interrupt.wr_data <= '0;
        if_cfg_interrupt.wr_addr <= '0;

        // tile cfg interface
        if_cfg_tile.wr_en <= '0;
        if_cfg_tile.wr_data <= '0;
        if_cfg_tile.wr_addr <= '0;
    end
    else if (wr_state == WR_IDLE) begin
        // clock gating
        cfg_wr_tile_clk_en_p <= 0;
        cfg_wr_interrupt_clk_en_p <= 0;

        // axi interface
        if_axil.awready <= '1;
        if_axil.wready <= '1;
        if_axil.bresp <= 2'b00;
        if_axil.bvalid <= '0;

        // interrupt cfg interface
        if_cfg_interrupt.wr_en <= '0;
        if_cfg_interrupt.wr_data <= '0;
        if_cfg_interrupt.wr_addr <= '0;

        // tile cfg interface
        if_cfg_tile.wr_en <= '0;
        if_cfg_tile.wr_data <= '0;
        if_cfg_tile.wr_addr <= '0;

        if (if_axil.awvalid & if_axil.awready) begin
            // awready to 0, wready to 1
            if_axil.awready <= 1'h0;
            if_axil.wready <= 1'h1;

            if (if_axil.awaddr[AXI_ADDR_WIDTH-1] == 1'b0) begin
                wr_state <= WR_REQ_INTERRUPT;
                // cfg interrupt clock gating off
                cfg_wr_interrupt_clk_en_p <= 1;
                if_cfg_interrupt.wr_addr <= if_axil.awaddr;
            end
            else begin
                wr_state <= WR_REQ_TILE;
                // cfg tile clock gating off
                cfg_wr_tile_clk_en_p <= 1;
                if_cfg_tile.wr_addr <= if_axil.awaddr;
            end
        end
        else if (if_axil.awvalid) begin
            if_axil.awready <= 1'h1;
        end
    end
    else if (wr_state == WR_REQ_INTERRUPT) begin
        if (if_axil.wvalid & if_axil.wready) begin
            if_axil.wready <= 1'h0;
            if_cfg_interrupt.wr_en <= 1'h1;
            if_cfg_interrupt.wr_data <= if_axil.wdata;
            wr_wait_cnt <= 'd0;
            wr_state <= WR_WAIT;
        end
    end
    else if (wr_state == WR_REQ_TILE) begin
        if (if_axil.wvalid & if_axil.wready) begin
            if_axil.wready <= 1'h0;
            if_cfg_tile.wr_en <= 1'h1;
            if_cfg_tile.wr_data <= if_axil.wdata;
            // TODO: Change it to dynamic depending on the tile id
            wr_wait_cnt <= 'd16;
            wr_state <= WR_WAIT;
        end
    end
    else if (wr_state == WR_WAIT) begin
        if_cfg_interrupt.wr_en <= 1'h0;
        if_cfg_tile.wr_en <= 1'h0;
        if (wr_wait_cnt == '0) begin
            if_axil.bvalid <= 1'h1;
            if_axil.bresp <= 2'b00;
            wr_state <= WR_RESP;
        end
        else begin
            wr_wait_cnt <= wr_wait_cnt - 1;
        end
    end
    else if (wr_state == WR_RESP) begin
        // clock gating on again
        cfg_wr_tile_clk_en_p <= 0;
        cfg_wr_interrupt_clk_en_p <= 0;

        if (if_axil.bready & if_axil.bvalid) begin
            if_axil.bvalid <= 1'h0;
            wr_state <= WR_IDLE;
        end
    end
end

//============================================================================//
// read fsm
//============================================================================//
always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        rd_state <= RD_IDLE;
        cfg_rd_is_tile <= '0;

        // clock gating on
        cfg_rd_tile_clk_en_p <= 0;
        cfg_rd_interrupt_clk_en_p <= 0;

        // axi interface
        if_axil.arready <= 1'h1;
        if_axil.rresp <= 2'b00;
        if_axil.rdata <= '0;

        // interrupt interface
        if_cfg_interrupt.rd_en <= 1'h0;
        if_cfg_interrupt.rd_addr <= '0;
        
        // tile interface
        if_cfg_tile.rd_en <= 1'h0;
        if_cfg_tile.rd_addr <= '0;
    end
    else if (rd_state == RD_IDLE) begin
        // clock gating on
        cfg_rd_tile_clk_en_p <= 0;
        cfg_rd_interrupt_clk_en_p <= 0;

        // axi interface
        if_axil.arready <= 1'h1;
        if_axil.rresp <= 2'b00;
        if_axil.rvalid <= 1'h0;

        // interrupt interface
        if_cfg_interrupt.rd_en <= 1'h0;
        if_cfg_interrupt.rd_addr <= '0;

        // tile interface
        if_cfg_tile.rd_en <= 1'h0;
        if_cfg_tile.rd_addr <= '0;

        if (if_axil.arvalid & if_axil.arready) begin
            if_axil.arready <= 1'h0;
            if (if_axil.araddr[AXI_ADDR_WIDTH-1] == 1'b0) begin
                // cfg interrupt clock gating off
                cfg_rd_interrupt_clk_en_p <= 1;

                rd_state <= RD_REQ_INTERRUPT;
                if_cfg_interrupt.rd_addr <= if_axil.araddr;
            end
            else begin
                // cfg tile clock gating off
                cfg_rd_tile_clk_en_p <= 1;

                rd_state <= RD_REQ_TILE;
                if_cfg_tile.rd_addr <= if_axil.araddr;
            end
        end
        else if (if_axil.arvalid) begin
            if_axil.arready <= 1'h1;
        end
    end
    else if (rd_state == RD_REQ_INTERRUPT) begin
        if_cfg_interrupt.rd_en <= 1'h1;
        rd_state <= RD_WAIT;
        cfg_rd_is_tile <= '0;
    end
    else if (rd_state == RD_REQ_TILE) begin
        if_cfg_tile.rd_en <= 1'h1;
        rd_state <= RD_WAIT;
        cfg_rd_is_tile <= '1;
    end
    else if (rd_state == RD_WAIT) begin
        if (cfg_rd_is_tile) begin
            if_cfg_tile.rd_en <= 1'h0;
            if (if_cfg_tile.rd_data_valid == 1'b1) begin
                if_axil.rdata <= if_cfg_tile.rd_data;
                if_axil.rvalid <= 1'h1;
                if_axil.rresp <= 2'b00;
                rd_state <= RD_RESP;
            end
        end
        else begin
            if_cfg_interrupt.rd_en <= 1'h0;
            if (if_cfg_interrupt.rd_data_valid == 1'b1) begin
                if_axil.rdata <= if_cfg_interrupt.rd_data;
                if_axil.rvalid <= 1'h1;
                if_axil.rresp <= 2'b00;
                rd_state <= RD_RESP;
            end
        end
    end
    else if (rd_state == RD_RESP) begin
        if (if_axil.rready & if_axil.rvalid) begin
            // clock gating on again
            cfg_rd_tile_clk_en_p <= 0;
            cfg_rd_interrupt_clk_en_p <= 0;

            if_axil.rvalid <= 1'h0;
            rd_state <= RD_IDLE;
        end
    end
end

//============================================================================//
// Half cycle shift of clock gating control signal
//============================================================================//
always_ff @(negedge clk or posedge reset) begin
    if (reset) begin
        cfg_wr_tile_clk_en <= 0;
        cfg_wr_interrupt_clk_en <= 0;
        cfg_rd_tile_clk_en <= 0;
        cfg_rd_interrupt_clk_en <= 0;
    end
    else begin
        cfg_wr_tile_clk_en <= cfg_wr_tile_clk_en_p;
        cfg_wr_interrupt_clk_en <= cfg_wr_interrupt_clk_en_p;
        cfg_rd_tile_clk_en <= cfg_rd_tile_clk_en_p;
        cfg_rd_interrupt_clk_en <= cfg_rd_interrupt_clk_en_p;
    end
end

endmodule
