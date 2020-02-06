/*=============================================================================
** Module: configuration interface
** Description:
**              Configuration interface
** Author: Taeyoung Kong
** Change history: 11/10/2019 - Implement first version of interface
**===========================================================================*/
`ifndef CFG_IFC
`define CFG_IFC

interface cfg_ifc #(
    parameter integer AWIDTH = 12,
    parameter integer DWIDTH = 32
);
    logic               wr_en;
    logic [AWIDTH-1:0]  wr_addr;
    logic [DWIDTH-1:0]  wr_data;
    logic               rd_en;
    logic [AWIDTH-1:0]  rd_addr;
    logic [DWIDTH-1:0]  rd_data;
    logic               rd_data_valid;

    modport slave(
        input  wr_en,
        input  wr_addr,
        input  wr_data,
        input  rd_en,
        input  rd_addr,
        output rd_data,
        output rd_data_valid
    );
   
    modport master (
        output wr_en,
        output wr_addr,
        output wr_data,
        output rd_en,
        output rd_addr,
        input  rd_data,
        input  rd_data_valid
    );

endinterface: cfg_ifc

`endif
