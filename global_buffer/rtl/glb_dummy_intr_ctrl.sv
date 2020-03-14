/*=============================================================================
** Module: glb_dummy_intr_ctrl.sv
** Description:
**              Global Buffer Interrupt Controller
** Author: Taeyoung Kong
** Change history: 02/02/2020 - Implement first version
**===========================================================================*/
import global_buffer_pkg::*;

module glb_dummy_intr_ctrl (
    input  logic                        clk,
    input  logic                        reset,

    axil_ifc.slave                      if_axil,
    cfg_ifc.slave                       if_cfg,

    input  logic [3*NUM_GLB_TILES-1:0]  interrupt_pulse_bundle,
    output logic                        interrupt
);

//============================================================================//
// internal variables
//============================================================================//
// TODO: assertion to check 2*NUM_GLB_TILES <= AXI_DATA_WIDTH
logic [3*NUM_GLB_TILES-1:0] int_ier;
logic [3*NUM_GLB_TILES-1:0] int_isr;

//============================================================================//
// int_ier (interrupt enable register)
// bit[2*tile_id + 0]: store dma interrupt enable register in glb_tile[tile_+id]
// bit[2*tile_id + 1]: load dma interrupt enable register in glb_tile[tile_+id]
//============================================================================//
always @(posedge clk or posedge reset) begin
    if (reset) begin
        int_ier <= '0;
    end
    else if (if_cfg.wr_clk_en) begin
        if (if_cfg.wr_en && if_cfg.wr_addr == AXI_ADDR_IER_1) begin
            int_ier[0 +: 2*NUM_GLB_TILES] <= if_cfg.wr_data[2*NUM_GLB_TILES-1:0];
        end
        else if (if_cfg.wr_en && if_cfg.wr_addr == AXI_ADDR_IER_2) begin
            int_ier[2*NUM_GLB_TILES +: NUM_GLB_TILES] <= if_cfg.wr_data[NUM_GLB_TILES-1:0];
        end
    end
end

//============================================================================//
// int_isr (interrupt status register)
// bit[NUM_GLB_TILES*0 + tile_id]: store dma interrupt status register in glb_tile
// bit[NUM_GLB_TILES*1 + tile_id]: load dma interrupt status register in glb_tile
// bit[NUM_GLB_TILES*2 + tile_id]: pc controller interrupt status register in glb_tile
//============================================================================//
always @(posedge clk or posedge reset) begin
    if (reset) begin
        int_isr <= '0;
    end
    else if (if_cfg.wr_clk_en) begin
        for (int i=0; i<2*NUM_GLB_TILES; i=i+1) begin
            if (int_ier[i] & interrupt_pulse_bundle[i]) begin
                int_isr[i] <= 1'b1;
            end
            else if (if_cfg.wr_en && if_cfg.wr_addr == AXI_ADDR_ISR_1) begin
                int_isr[i] <= int_isr[i] ^ if_cfg.wr_data[i]; // toggle on write
            end
        end
        for (int i=2*NUM_GLB_TILES; i<3*NUM_GLB_TILES; i=i+1) begin
            if (int_ier[i] & interrupt_pulse_bundle[i]) begin
                int_isr[i] <= 1'b1;
            end
            else if (if_cfg.wr_en && if_cfg.wr_addr == AXI_ADDR_ISR_2) begin
                int_isr[i] <= int_isr[i] ^ if_cfg.wr_data[(i-2*NUM_GLB_TILES)]; // toggle on write
            end
        end
    end
end

//============================================================================//
// int_isr (interrupt status register)
// bit[NUM_GLB_TILES*0 + tile_id]: store dma interrupt status register in glb_tile
// bit[NUM_GLB_TILES*1 + tile_id]: load dma interrupt status register in glb_tile
// bit[NUM_GLB_TILES*2 + tile_id]: pc controller interrupt status register in glb_tile
//============================================================================//
always @(posedge clk or posedge reset) begin
    if (reset) begin
        int_isr <= '0;
    end
    else if (if_cfg.wr_clk_en) begin
        for (int i=0; i<2*NUM_GLB_TILES; i=i+1) begin
            if (int_ier[i] & interrupt_pulse_bundle[i]) begin
                int_isr[i] <= 1'b1;
            end
            else if (if_cfg.wr_en && if_cfg.wr_addr == AXI_ADDR_ISR_1) begin
                int_isr[i] <= int_isr[i] ^ if_cfg.wr_data[i]; // toggle on write
            end
        end
        for (int i=2*NUM_GLB_TILES; i<3*NUM_GLB_TILES; i=i+1) begin
            if (int_ier[i] & interrupt_pulse_bundle[i]) begin
                int_isr[i] <= 1'b1;
            end
            else if (if_cfg.wr_en && if_cfg.wr_addr == AXI_ADDR_ISR_2) begin
                int_isr[i] <= int_isr[i] ^ if_cfg.wr_data[(i-2*NUM_GLB_TILES)]; // toggle on write
            end
        end
    end
end

//============================================================================//
// interrupt signal
//============================================================================//
assign interrupt = |int_isr;

//============================================================================//
// Read CGRA control registers
//============================================================================//
always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
        if_cfg.rd_data <= 0;
        if_cfg.rd_data_valid <= 0;
    end
    else if (if_cfg.rd_clk_en) begin
        if (if_cfg.rd_en) begin
            if_cfg.rd_data_valid <= 1;
            case (if_cfg.rd_addr)
                AXI_ADDR_IER_1: if_cfg.rd_data <= int_ier[2*NUM_GLB_TILES-1:0];
                AXI_ADDR_IER_2: if_cfg.rd_data <= int_ier[NUM_GLB_TILES-1:0];
                AXI_ADDR_ISR_1: if_cfg.rd_data <= int_isr[2*NUM_GLB_TILES-1:0];
                AXI_ADDR_ISR_2: if_cfg.rd_data <= int_isr[NUM_GLB_TILES-1:0];
                default: if_cfg.rd_data <= 0;
            endcase
        end
        else begin
            if_cfg.rd_data_valid <= 0;
        end
    end
end

endmodule
