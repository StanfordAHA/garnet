/*=============================================================================
** Module: strm_ifc.sv
** Description:
**              interface for streaming packet
** Author: Taeyoung Kong
** Change history:
**  04/18/2020 - Implement first version
**===========================================================================*/

interface strm_ifc(input logic clk);

    // declare the signals
    logic strm_start_pulse;
    logic strm_f2g_interrupt;
    logic strm_g2f_interrupt;

    logic [CGRA_PER_GLB-1:0][CGRA_DATA_WIDTH-1:0] data_f2g;
    logic [CGRA_PER_GLB-1:0]                      data_valid_f2g;

    logic [CGRA_PER_GLB-1:0][CGRA_DATA_WIDTH-1:0] data_g2f;
    logic [CGRA_PER_GLB-1:0]                      data_valid_g2f;

    modport glb (
        input  clk, strm_start_pulse,
        input  data_f2g, data_valid_f2g,
        output data_g2f, data_valid_g2f,
        output strm_f2g_interrupt, strm_g2f_interrupt
    );

    clocking cbd @(posedge clk);
        output strm_start_pulse;
        output data_f2g, data_valid_f2g;
        input  data_g2f, data_valid_g2f;
        input  strm_f2g_interrupt, strm_g2f_interrupt;
    endclocking : cbd
    modport driver (clocking cbd);

    clocking cbm @(posedge clk);
        input strm_start_pulse, strm_f2g_interrupt, strm_g2f_interrupt, data_f2g, data_valid_f2g, data_g2f, data_valid_g2f;
    endclocking : cbm
    modport monitor (clocking cbm);

endinterface

typedef virtual strm_ifc vStrmIfc;
typedef virtual strm_ifc.driver vStrmIfcDriver;
typedef virtual strm_ifc.monitor vStrmIfcMonitor;
