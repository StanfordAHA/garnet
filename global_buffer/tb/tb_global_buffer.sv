/*=============================================================================
** Module: tb_global_buffer.sv
** Description:
**              testbench for global buffer
** Author: Taeyoung Kong
** Change history:  02/03/2020 - Implement first version of testbench
**===========================================================================*/
import global_buffer_pkg::*;

module tb_global_buffer();
    logic                           clk;
    logic                           clk_en;
    logic                           reset;

    logic [CGRA_DATA_WIDTH-1:0]     stream_data_f2g [NUM_TILES];
    logic                           stream_data_valid_f2g [NUM_TILES];

    logic                           interrupt;

//============================================================================//
// Instantiate clocks
//============================================================================//
    clocker clocker_inst (
        .clk(clk),
        .reset(reset)
    );

//============================================================================//
// Initial
//============================================================================//
    initial begin
        repeat(100000) @(posedge clk);
        $display("\n%0t\tERROR: The 100000 cycles marker has passed!", $time);
        $finish(2);
    end

    initial begin
        clk_en = 1'b1;
    end

//============================================================================//
// Instantiate interface
//============================================================================//
    axil_ifc #(
        .AXI_AWIDTH(AXI_ADDR_WIDTH),
        .AXI_DWIDTH(AXI_DATA_WIDTH)
    ) if_axil ();

//============================================================================//
// Instantiate dut
//============================================================================//
    global_buffer dut_global_buffer (
        .if_axil (if_axil),
        .*
    );

//============================================================================//
// Instantiate test_global_buffer
//============================================================================//
    tb_global_buffer_prog prog (
        .if_axil (if_axil),
        .*
    );

endmodule
