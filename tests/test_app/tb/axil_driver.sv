`define DBG_AXILDRIVER 0  // Set to '1' for debugging

// If protocol is broken, can shorten SLAVE_WAIT timeout for debugging (10 is a good number)
`define SLAVE_WAIT 100

// Can use same global addr and data for everybody because there are only three forks:
// - one in wait_interrupt has a mem read, but
//   - addr is same for all forks, and
//   - data keeps getting overwritten, but we only care about the last one
// - one in Env_run() is disabled and throws an error if anyone ever tries to use it;
// - one in ProcDriver_read_data() does not use addr/data for reads

bit [CGRA_AXI_ADDR_WIDTH-1:0] addr;
bit [CGRA_AXI_DATA_WIDTH-1:0] data;

Config AxilDriver_cfg[];
task AxilDriver_config_write();
    foreach (AxilDriver_cfg[i]) begin
        addr = AxilDriver_cfg[i].addr;
        data = AxilDriver_cfg[i].data;
        AxilDriver_write();
    end
endtask

semaphore axil_lock; initial axil_lock = new(1);
task AxilDriver_write();
    if (`DBG_AXILDRIVER) $display("[%0t] AXI-Lite Write. Addr: %08h, Data: %08h", $time, addr, data);

    // Note: "slave not ready" timout will occur b/c awready stays false until data is read (below)
    // awready advances controller state from WAIT(0) to WR_REQ_GLC(1)

    axil_lock.get(1);
    @(posedge axil_ifc.clk);  // added to match non-clocking timing...
    @(posedge axil_ifc.clk);
    axil_ifc.awaddr  = addr;
    axil_ifc.awvalid = 1'b1;
    // FIXME?? seems like this should happen BEFORE setting awvalid etc. above? First ready, then valid?
    for (int i = 0; i < `SLAVE_WAIT; i++) begin
        if (axil_ifc.awready == 1) break;
        @(posedge axil_ifc.clk);
        if (i == (`SLAVE_WAIT-1)) $display("axi slave is not ready 1");
    end
    @(posedge axil_ifc.clk);
    axil_ifc.awvalid = 1'b0;
    @(posedge axil_ifc.clk);
    // Axi controller should now be in state 1 (WR_REQ_GLC==1, see glc_axi_ctrl.sv) // 132ns
    axil_ifc.wdata  = data;
    axil_ifc.wvalid = 1'b1;
    // Axi controller should now be in state 3 (WR_WAIT)  // 132ns
    // Then, after one cycle, on to state 4 (WR_RESP)     // 133ns
    // where it stays until wr_wait_cnt counts from clog2(14) down to zero
    for (int i = 0; i < `SLAVE_WAIT; i++) begin
        if (axil_ifc.wready == 1) break;
        @(posedge axil_ifc.clk);
        if (i == (`SLAVE_WAIT-1)) $display("axi slave is not ready 2");  // ~152ns
    end
    @(posedge axil_ifc.clk);  // Axi controller should now be in state 0 (WR_IDLE)   // 153ns
    axil_ifc.wvalid = 1'b0;
    axil_ifc.bready = 1'b1;
    for (int i = 0; i < `SLAVE_WAIT; i++) begin
        if (axil_ifc.bvalid == 1) break;
        @(posedge axil_ifc.clk);
        if (i == (`SLAVE_WAIT-1)) $display("axi slave is not ready 3");
    end
    @(posedge axil_ifc.clk);
    axil_ifc.bready = 0;   // 164ns
    @(posedge axil_ifc.clk);
    axil_lock.put(1);
endtask

task AxilDriver_read();
    axil_lock.get(1);

    @(posedge axil_ifc.clk);
    axil_ifc.araddr  = addr;
    axil_ifc.arvalid = 1'b1;
    axil_ifc.rready  = 1;
    for (int i = 0; i < `SLAVE_WAIT; i++) begin
        if (axil_ifc.arready == 1) break;
        @(posedge axil_ifc.clk);
        if (i == (`SLAVE_WAIT-1)) $display("axi slave is not ready 1");
    end
    @(posedge axil_ifc.clk);
    axil_ifc.arvalid = 0;
    @(posedge axil_ifc.clk);
    for (int i = 0; i < `SLAVE_WAIT; i++) begin
        if (axil_ifc.rvalid == 1) break;
        @(posedge axil_ifc.clk);
        if (i == (`SLAVE_WAIT-1)) $display("axi slave is not ready 2");
    end
    data = axil_ifc.rdata;
    @(posedge axil_ifc.clk);
    axil_ifc.rready = 0;      // 5970.5ns
    @(posedge axil_ifc.clk);
    if (`DBG_AXILDRIVER) $display("[%0t] AXI-Lite Read. Addr: %08h, Data: %08h", $time, addr, data);
    axil_lock.put(1);
endtask

