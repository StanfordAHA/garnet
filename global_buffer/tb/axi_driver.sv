/*=============================================================================
** Module: axi_driver.sv
** Description:
**              driver for the axi interface
** Author: Taeyoung Kong
** Change history:  10/22/2019 - Implement first version of axi driver
**===========================================================================*/

typedef struct {
    logic [AXI_DATA_WIDTH-1:0] wr_data;
    logic [AXI_DATA_WIDTH-1:0] rd_data;
    logic [AXI_ADDR_WIDTH-1:0] addr;
} axi_trans_t;

//============================================================================//
// Class axi_driver
//============================================================================//
class axi_driver;
    bit clk;
    virtual axil_ifc.test ifc; // interface for the axi signals

    // current transaction 
    axi_trans_t cur_trans;
   
    function new(input bit clk, virtual axil_ifc.test ifc);
        this.ifc = ifc;
        this.clk = clk;
    endfunction 

    // Extern tasks in axi driver
    // write axi instruction
    extern task Write(input axi_trans_t new_trans);
    extern task axi_write(input [AXI_ADDR_WIDTH-1:0] addr, input [AXI_DATA_WIDTH-1:0] data);
    // read axi instruction
    extern task Read(input axi_trans_t new_trans);
    extern task axi_read(input [AXI_ADDR_WIDTH-1:0] addr);

    // get the results of the latest transaction sent
    extern function axi_trans_t GetResult();

    // reset
    extern task Reset();

endclass: axi_driver


//============================================================================//
// Axi driver function
// Get the results of the latest transaction sent
//============================================================================//
function axi_trans_t axi_driver::GetResult();
    return cur_trans;
endfunction // axi_trans_t
   
//============================================================================//
// AXI transaction task
//============================================================================//
task axi_driver::Reset();
    repeat (2) @(posedge this.clk);
    this.ifc.awaddr = 0;
    this.ifc.awvalid = 0;
    this.ifc.wdata = 0;
    this.ifc.wvalid = 0;
    this.ifc.bready = 0;
    this.ifc.araddr = 0;
    this.ifc.arvalid = 0;
    this.ifc.rready = 0;
    this.ifc.wstrb = 0;
    this.ifc.arprot = 0;
    this.ifc.awprot = 0;
    repeat (2) @(posedge this.clk);
endtask // Reset

task axi_driver::Write(input axi_trans_t new_trans);
    cur_trans = new_trans;

    @(posedge this.clk);
    this.ifc.awaddr = cur_trans.addr;
    this.ifc.awvalid = 1;

    for (int i=0; i<100; i++) begin
        if (this.ifc.awready==1) break;
        @(posedge this.clk);
    end

    @(posedge this.clk);
    this.ifc.awvalid = 0;

    @(posedge this.clk);
    this.ifc.wdata = cur_trans.wr_data;
    this.ifc.wvalid = 1;
    for (int i=0; i<100; i++) begin
        if (this.ifc.wready==1) break;
        @(posedge this.clk);
    end

    @(posedge this.clk);
    this.ifc.wvalid = 0;
    this.ifc.bready = 1;
    for (int i=0; i<100; i++) begin
        if (this.ifc.bvalid==1) break;
        @(posedge this.clk);
    end
    @(posedge this.clk);
    this.ifc.bready = 0;
    @(posedge this.clk);
endtask // Write

task axi_driver::Read(input axi_trans_t new_trans);
    cur_trans = new_trans;

    @(posedge this.clk);
    this.ifc.araddr = cur_trans.addr;
    this.ifc.arvalid = 1;
    this.ifc.rready = 1;

    for (int i=0; i<100; i++) begin
        if (this.ifc.arready==1) break;
        @(posedge this.clk);
    end

    @(posedge this.clk);
    this.ifc.arvalid = 0;

    @(posedge this.clk);
    for (int i=0; i<100; i++) begin
        if (this.ifc.rvalid==1) break;
        @(posedge this.clk);
    end

    cur_trans.rd_data = this.ifc.rdata;
    @(posedge this.clk);
    this.ifc.rready = 0;
    @(posedge this.clk);
endtask // Read

task axi_driver::axi_write(input [AXI_ADDR_WIDTH-1:0] addr, input [AXI_DATA_WIDTH-1:0] data);
    axi_trans_t axi_trans;
    axi_trans.addr = addr;
    axi_trans.wr_data = data;
    Write(axi_trans);
endtask // axi_write

task axi_driver::axi_read(input [AXI_ADDR_WIDTH-1:0] addr);
    axi_trans_t axi_trans;
    axi_trans.addr = addr;
    Read(axi_trans);
endtask // axi_read

