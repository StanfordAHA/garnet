/*=============================================================================
** Module: configuration interface
** Description:
**              Configuration interface
** Author: Taeyoung Kong
** Change history: 11/10/2019 - Implement first version of interface
**===========================================================================*/
interface cfg_ifc #(
    parameter integer AWIDTH = 32,
    parameter integer DWIDTH = 32
)
    logic               wr_en;
    logic               rd_en;
    logic [AWIDTH-1:0]  addr;
    logic [DWIDTH-1:0]  wr_data;
    logic [DWIDTH-1:0]  rd_data;

    modport slave(
        input   wr_en,
        input   rd_en,
        input   addr,
        input   wr_data,
        output  rd_data
    );
   
    modport master (
        output  wr_en,
        output  rd_en,
        output  addr,
        output  wr_data,
        input   rd_data
    );
   
    modport test (
        output  wr_en,
        output  rd_en,
        output  addr,
        output  wr_data,
        input   rd_data
    );

endinterface: cfg_ifc
