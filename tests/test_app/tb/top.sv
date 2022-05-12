/*=============================================================================
** Module: top.sv
** Description:
**              top for garnet testbench
** Author: Taeyoung Kong
** Change history:
**  10/14/2020 - Implement the first version
**===========================================================================*/
`ifndef CLK_PERIOD
`define CLK_PERIOD 1ns
`endif

import global_buffer_param::*;

module top;
    timeunit 1ns; timeprecision 1ps;

    logic clk;
    logic reset;
    logic interrupt;

    //============================================================================//
    // clk / reset generation
    //============================================================================//
    // clk generation
    initial begin
        clk = 0;
        forever #(`CLK_PERIOD / 2.0) clk = !clk;
    end

    // reset generation
    initial begin
        reset <= 1;
        repeat (3) @(posedge clk);
        reset <= 0;
    end

    // sdf annotation
    /*initial begin
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X00_Y0A,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X00_Y0B,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X00_Y0C,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X00_Y0D,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X00_Y0E,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X00_Y0F,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X00_Y01,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X00_Y02,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X00_Y03,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X00_Y04,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X00_Y05,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X00_Y06,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X00_Y07,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X00_Y08,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X00_Y09,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X00_Y10,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X0A_Y0A,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X0A_Y0B,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X0A_Y0C,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X0A_Y0D,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X0A_Y0E,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X0A_Y0F,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X0A_Y01,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X0A_Y02,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X0A_Y03,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X0A_Y04,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X0A_Y05,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X0A_Y06,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X0A_Y07,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X0A_Y08,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X0A_Y09,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X0A_Y10,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X0C_Y0A,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X0C_Y0B,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X0C_Y0C,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X0C_Y0D,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X0C_Y0E,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X0C_Y0F,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X0C_Y01,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X0C_Y02,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X0C_Y03,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X0C_Y04,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X0C_Y05,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X0C_Y06,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X0C_Y07,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X0C_Y08,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X0C_Y09,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X0C_Y10,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X0D_Y0A,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X0D_Y0B,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X0D_Y0C,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X0D_Y0D,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X0D_Y0E,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X0D_Y0F,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X0D_Y01,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X0D_Y02,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X0D_Y03,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X0D_Y04,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X0D_Y05,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X0D_Y06,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X0D_Y07,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X0D_Y08,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X0D_Y09,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X0D_Y10,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X0E_Y0A,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X0E_Y0B,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X0E_Y0C,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X0E_Y0D,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X0E_Y0E,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X0E_Y0F,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X0E_Y01,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X0E_Y02,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X0E_Y03,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X0E_Y04,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X0E_Y05,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X0E_Y06,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X0E_Y07,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X0E_Y08,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X0E_Y09,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X0E_Y10,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X01_Y0A,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X01_Y0B,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X01_Y0C,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X01_Y0D,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X01_Y0E,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X01_Y0F,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X01_Y01,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X01_Y02,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X01_Y03,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X01_Y04,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X01_Y05,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X01_Y06,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X01_Y07,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X01_Y08,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X01_Y09,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X01_Y10,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X1A_Y0A,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X1A_Y0B,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X1A_Y0C,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X1A_Y0D,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X1A_Y0E,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X1A_Y0F,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X1A_Y01,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X1A_Y02,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X1A_Y03,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X1A_Y04,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X1A_Y05,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X1A_Y06,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X1A_Y07,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X1A_Y08,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X1A_Y09,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X1A_Y10,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X1C_Y0A,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X1C_Y0B,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X1C_Y0C,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X1C_Y0D,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X1C_Y0E,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X1C_Y0F,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X1C_Y01,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X1C_Y02,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X1C_Y03,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X1C_Y04,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X1C_Y05,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X1C_Y06,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X1C_Y07,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X1C_Y08,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X1C_Y09,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X1C_Y10,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X1D_Y0A,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X1D_Y0B,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X1D_Y0C,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X1D_Y0D,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X1D_Y0E,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X1D_Y0F,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X1D_Y01,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X1D_Y02,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X1D_Y03,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X1D_Y04,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X1D_Y05,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X1D_Y06,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X1D_Y07,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X1D_Y08,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X1D_Y09,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X1D_Y10,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X1E_Y0A,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X1E_Y0B,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X1E_Y0C,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X1E_Y0D,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X1E_Y0E,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X1E_Y0F,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X1E_Y01,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X1E_Y02,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X1E_Y03,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X1E_Y04,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X1E_Y05,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X1E_Y06,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X1E_Y07,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X1E_Y08,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X1E_Y09,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X1E_Y10,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X02_Y0A,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X02_Y0B,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X02_Y0C,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X02_Y0D,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X02_Y0E,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X02_Y0F,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X02_Y01,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X02_Y02,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X02_Y03,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X02_Y04,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X02_Y05,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X02_Y06,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X02_Y07,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X02_Y08,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X02_Y09,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X02_Y10,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X04_Y0A,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X04_Y0B,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X04_Y0C,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X04_Y0D,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X04_Y0E,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X04_Y0F,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X04_Y01,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X04_Y02,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X04_Y03,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X04_Y04,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X04_Y05,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X04_Y06,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X04_Y07,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X04_Y08,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X04_Y09,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X04_Y10,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X05_Y0A,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X05_Y0B,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X05_Y0C,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X05_Y0D,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X05_Y0E,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X05_Y0F,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X05_Y01,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X05_Y02,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X05_Y03,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X05_Y04,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X05_Y05,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X05_Y06,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X05_Y07,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X05_Y08,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X05_Y09,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X05_Y10,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X06_Y0A,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X06_Y0B,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X06_Y0C,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X06_Y0D,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X06_Y0E,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X06_Y0F,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X06_Y01,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X06_Y02,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X06_Y03,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X06_Y04,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X06_Y05,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X06_Y06,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X06_Y07,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X06_Y08,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X06_Y09,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X06_Y10,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X08_Y0A,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X08_Y0B,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X08_Y0C,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X08_Y0D,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X08_Y0E,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X08_Y0F,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X08_Y01,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X08_Y02,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X08_Y03,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X08_Y04,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X08_Y05,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X08_Y06,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X08_Y07,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X08_Y08,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X08_Y09,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X08_Y10,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X09_Y0A,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X09_Y0B,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X09_Y0C,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X09_Y0D,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X09_Y0E,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X09_Y0F,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X09_Y01,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X09_Y02,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X09_Y03,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X09_Y04,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X09_Y05,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X09_Y06,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X09_Y07,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X09_Y08,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X09_Y09,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X09_Y10,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X10_Y0A,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X10_Y0B,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X10_Y0C,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X10_Y0D,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X10_Y0E,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X10_Y0F,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X10_Y01,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X10_Y02,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X10_Y03,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X10_Y04,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X10_Y05,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X10_Y06,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X10_Y07,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X10_Y08,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X10_Y09,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X10_Y10,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X11_Y0A,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X11_Y0B,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X11_Y0C,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X11_Y0D,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X11_Y0E,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X11_Y0F,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X11_Y01,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X11_Y02,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X11_Y03,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X11_Y04,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X11_Y05,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X11_Y06,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X11_Y07,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X11_Y08,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X11_Y09,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X11_Y10,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X12_Y0A,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X12_Y0B,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X12_Y0C,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X12_Y0D,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X12_Y0E,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X12_Y0F,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X12_Y01,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X12_Y02,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X12_Y03,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X12_Y04,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X12_Y05,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X12_Y06,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X12_Y07,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X12_Y08,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X12_Y09,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X12_Y10,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X14_Y0A,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X14_Y0B,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X14_Y0C,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X14_Y0D,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X14_Y0E,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X14_Y0F,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X14_Y01,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X14_Y02,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X14_Y03,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X14_Y04,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X14_Y05,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X14_Y06,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X14_Y07,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X14_Y08,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X14_Y09,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X14_Y10,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X15_Y0A,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X15_Y0B,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X15_Y0C,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X15_Y0D,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X15_Y0E,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X15_Y0F,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X15_Y01,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X15_Y02,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X15_Y03,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X15_Y04,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X15_Y05,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X15_Y06,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X15_Y07,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X15_Y08,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X15_Y09,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X15_Y10,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X16_Y0A,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X16_Y0B,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X16_Y0C,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X16_Y0D,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X16_Y0E,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X16_Y0F,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X16_Y01,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X16_Y02,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X16_Y03,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X16_Y04,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X16_Y05,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X16_Y06,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X16_Y07,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X16_Y08,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X16_Y09,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X16_Y10,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X18_Y0A,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X18_Y0B,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X18_Y0C,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X18_Y0D,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X18_Y0E,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X18_Y0F,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X18_Y01,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X18_Y02,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X18_Y03,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X18_Y04,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X18_Y05,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X18_Y06,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X18_Y07,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X18_Y08,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X18_Y09,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X18_Y10,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X19_Y0A,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X19_Y0B,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X19_Y0C,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X19_Y0D,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X19_Y0E,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X19_Y0F,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X19_Y01,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X19_Y02,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X19_Y03,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X19_Y04,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X19_Y05,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X19_Y06,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X19_Y07,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X19_Y08,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X19_Y09,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_PE.sdf", top.dut.Interconnect_inst0.Tile_X19_Y10,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X0B_Y0A,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X0B_Y0B,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X0B_Y0C,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X0B_Y0D,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X0B_Y0E,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X0B_Y0F,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X0B_Y01,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X0B_Y02,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X0B_Y03,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X0B_Y04,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X0B_Y05,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X0B_Y06,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X0B_Y07,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X0B_Y08,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X0B_Y09,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X0B_Y10,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X0F_Y0A,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X0F_Y0B,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X0F_Y0C,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X0F_Y0D,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X0F_Y0E,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X0F_Y0F,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X0F_Y01,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X0F_Y02,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X0F_Y03,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X0F_Y04,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X0F_Y05,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X0F_Y06,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X0F_Y07,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X0F_Y08,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X0F_Y09,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X0F_Y10,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X1B_Y0A,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X1B_Y0B,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X1B_Y0C,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X1B_Y0D,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X1B_Y0E,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X1B_Y0F,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X1B_Y01,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X1B_Y02,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X1B_Y03,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X1B_Y04,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X1B_Y05,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X1B_Y06,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X1B_Y07,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X1B_Y08,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X1B_Y09,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X1B_Y10,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X1F_Y0A,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X1F_Y0B,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X1F_Y0C,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X1F_Y0D,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X1F_Y0E,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X1F_Y0F,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X1F_Y01,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X1F_Y02,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X1F_Y03,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X1F_Y04,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X1F_Y05,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X1F_Y06,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X1F_Y07,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X1F_Y08,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X1F_Y09,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X1F_Y10,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X03_Y0A,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X03_Y0B,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X03_Y0C,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X03_Y0D,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X03_Y0E,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X03_Y0F,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X03_Y01,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X03_Y02,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X03_Y03,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X03_Y04,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X03_Y05,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X03_Y06,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X03_Y07,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X03_Y08,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X03_Y09,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X03_Y10,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X07_Y0A,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X07_Y0B,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X07_Y0C,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X07_Y0D,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X07_Y0E,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X07_Y0F,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X07_Y01,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X07_Y02,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X07_Y03,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X07_Y04,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X07_Y05,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X07_Y06,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X07_Y07,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X07_Y08,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X07_Y09,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X07_Y10,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X13_Y0A,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X13_Y0B,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X13_Y0C,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X13_Y0D,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X13_Y0E,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X13_Y0F,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X13_Y01,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X13_Y02,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X13_Y03,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X13_Y04,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X13_Y05,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X13_Y06,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X13_Y07,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X13_Y08,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X13_Y09,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X13_Y10,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X17_Y0A,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X17_Y0B,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X17_Y0C,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X17_Y0D,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X17_Y0E,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X17_Y0F,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X17_Y01,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X17_Y02,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X17_Y03,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X17_Y04,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X17_Y05,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X17_Y06,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X17_Y07,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X17_Y08,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X17_Y09,,,"MAXIMUM");
        $sdf_annotate("./netlist/Tile_MemCore.sdf", top.dut.Interconnect_inst0.Tile_X17_Y10,,,"MAXIMUM");

        $sdf_annotate("./netlist/tile_array.sdf",top.dut.Interconnect_inst0,,,"MAXIMUM");

        $sdf_annotate("./netlist/glb_tile.sdf",top.dut.global_buffer_W_inst0.global_buffer.glb_tile_gen_0 ,,,"MAXIMUM");
        $sdf_annotate("./netlist/glb_tile.sdf",top.dut.global_buffer_W_inst0.global_buffer.glb_tile_gen_1 ,,,"MAXIMUM");
        $sdf_annotate("./netlist/glb_tile.sdf",top.dut.global_buffer_W_inst0.global_buffer.glb_tile_gen_2 ,,,"MAXIMUM");
        $sdf_annotate("./netlist/glb_tile.sdf",top.dut.global_buffer_W_inst0.global_buffer.glb_tile_gen_3 ,,,"MAXIMUM");
        $sdf_annotate("./netlist/glb_tile.sdf",top.dut.global_buffer_W_inst0.global_buffer.glb_tile_gen_4 ,,,"MAXIMUM");
        $sdf_annotate("./netlist/glb_tile.sdf",top.dut.global_buffer_W_inst0.global_buffer.glb_tile_gen_5 ,,,"MAXIMUM");
        $sdf_annotate("./netlist/glb_tile.sdf",top.dut.global_buffer_W_inst0.global_buffer.glb_tile_gen_6 ,,,"MAXIMUM");
        $sdf_annotate("./netlist/glb_tile.sdf",top.dut.global_buffer_W_inst0.global_buffer.glb_tile_gen_7 ,,,"MAXIMUM");
        $sdf_annotate("./netlist/glb_tile.sdf",top.dut.global_buffer_W_inst0.global_buffer.glb_tile_gen_8 ,,,"MAXIMUM");
        $sdf_annotate("./netlist/glb_tile.sdf",top.dut.global_buffer_W_inst0.global_buffer.glb_tile_gen_9 ,,,"MAXIMUM");
        $sdf_annotate("./netlist/glb_tile.sdf",top.dut.global_buffer_W_inst0.global_buffer.glb_tile_gen_10 ,,,"MAXIMUM");
        $sdf_annotate("./netlist/glb_tile.sdf",top.dut.global_buffer_W_inst0.global_buffer.glb_tile_gen_11 ,,,"MAXIMUM");
        $sdf_annotate("./netlist/glb_tile.sdf",top.dut.global_buffer_W_inst0.global_buffer.glb_tile_gen_12 ,,,"MAXIMUM");
        $sdf_annotate("./netlist/glb_tile.sdf",top.dut.global_buffer_W_inst0.global_buffer.glb_tile_gen_13 ,,,"MAXIMUM");
        $sdf_annotate("./netlist/glb_tile.sdf",top.dut.global_buffer_W_inst0.global_buffer.glb_tile_gen_14 ,,,"MAXIMUM");
        $sdf_annotate("./netlist/glb_tile.sdf",top.dut.global_buffer_W_inst0.global_buffer.glb_tile_gen_15 ,,,"MAXIMUM");

        $sdf_annotate("./netlist/glb_top.sdf",top.dut.global_buffer_W_inst0.global_buffer,,,"MAXIMUM");

        $sdf_annotate("./netlist/global_controller.sdf",top.dut.GlobalController_cfg_32_32_axi_13_32_inst0$global_controller_inst0);

//$sdf_annotate("netlist/design.sdf",Tbench.u_soc,,"sdf_soc.log","MAXIMUM");

    end*/

    //============================================================================//
    // interfaces
    //============================================================================//
    proc_ifc p_ifc (.clk(clk));
    axil_ifc #(
        .ADDR_WIDTH(CGRA_AXI_ADDR_WIDTH),
        .DATA_WIDTH(CGRA_AXI_DATA_WIDTH)
    ) axil_ifc (
        .clk(clk)
    );

    //============================================================================//
    // instantiate test
    //============================================================================//
    garnet_test test (
        .clk     (clk),
        .reset   (reset),
        .p_ifc   (p_ifc),
        .axil_ifc(axil_ifc)
    );

    //============================================================================//
    // instantiate dut
    //============================================================================//
    GarnetSOC_pad_frame_Garnet dut (
    //Garnet dut (
        // clk/reset/interrupt
        .clk_in              (clk),
        .clk_in_clone1              (clk),
        .clk_in_clone2              (clk),
        .reset_in            (reset),
        .interrupt           (interrupt),
        .cgra_running_clk_out(  /*unused*/),

        // proc ifc
        .proc_packet_wr_en        (p_ifc.wr_en),
        .proc_packet_wr_strb      (p_ifc.wr_strb),
        .proc_packet_wr_addr      (p_ifc.wr_addr),
        .proc_packet_wr_data      (p_ifc.wr_data),
        .proc_packet_rd_en        (p_ifc.rd_en),
        .proc_packet_rd_addr      (p_ifc.rd_addr),
        .proc_packet_rd_data      (p_ifc.rd_data),
        .proc_packet_rd_data_valid(p_ifc.rd_data_valid),

        // axi4-lite ifc
        .axi4_slave_araddr (axil_ifc.araddr),
        .axi4_slave_arready(axil_ifc.arready),
        .axi4_slave_arvalid(axil_ifc.arvalid),
        .axi4_slave_awaddr (axil_ifc.awaddr),
        .axi4_slave_awready(axil_ifc.awready),
        .axi4_slave_awvalid(axil_ifc.awvalid),
        .axi4_slave_bready (axil_ifc.bready),
        .axi4_slave_bresp  (axil_ifc.bresp),
        .axi4_slave_bvalid (axil_ifc.bvalid),
        .axi4_slave_rdata  (axil_ifc.rdata),
        .axi4_slave_rready (axil_ifc.rready),
        .axi4_slave_rresp  (axil_ifc.rresp),
        .axi4_slave_rvalid (axil_ifc.rvalid),
        .axi4_slave_wdata  (axil_ifc.wdata),
        .axi4_slave_wready (axil_ifc.wready),
        .axi4_slave_wvalid (axil_ifc.wvalid),

        // jtag ifc
        .jtag_tck   (  /*unused*/),
        .jtag_tdi   (  /*unused*/),
        .jtag_tdo   (  /*unused*/),
        .jtag_tms   (  /*unused*/),
        .jtag_trst_n(  /*unused*/)
    );


endmodule
