// class AxilDriver;

// function AxilDriver::new(vAxilIfcDriver vif, semaphore axil_lock);
// => NO LONGER NEEDED

// task AxilDriver::config_write(Config cfg[]);
Config AxilDriver_cfg[];
task AxilDriver_config_write();
    foreach (AxilDriver_cfg[i]) begin
        // write(AxilDriver_cfg[i].addr, AxilDriver_cfg[i].data);
        addr = AxilDriver_cfg[i].addr;
        data = AxilDriver_cfg[i].data;
        AxilDriver_write();
    end
endtask

// task AxilDriver::write(bit [CGRA_AXI_ADDR_WIDTH-1:0] addr, data);
semaphore axil_lock; initial axil_lock = new(1);
bit [CGRA_AXI_ADDR_WIDTH-1:0] AxilDriver_write_addr;
bit [CGRA_AXI_DATA_WIDTH-1:0] AxilDriver_write_data;
task AxilDriver_write();
   AxilDriver_write_addr = addr;
   AxilDriver_write_data = data;

   ////////////////////////////////////////////////////////////////////////
   // $display("AXI-Lite Write. Addr: %08h, Data: %08h", addr, data);
   // axil_lock.get(1);

   $display("[%0t] AXI-Lite Write. Addr: %08h, Data: %08h",
            $time, AxilDriver_write_addr, AxilDriver_write_data);

   // semaphore axil_lock;
   $display("AxilDriver_write() wants the lock"); $fflush();
   axil_lock.get(1);
   $display("AxilDriver_write() got the lock"); $fflush();

   ////////////////////////////////////////////////////////////////////////
   // @(vif.cbd);
   // vif.cbd.awaddr  <= addr;
   // vif.cbd.awvalid <= 1'b1;
   // for (int i = 0; i < 100; i++) begin
   //     if (vif.cbd.awready == 1) break;
   //     @(vif.cbd);
   //     if (i == 99) return;  // axi slave is not ready
   // end
   // @(vif.cbd);
   // vif.cbd.awvalid <= 0;

   // Note: "slave not ready" timout will occur b/c awready stays false until data is read (below)
   // awready advances controller state from WAIT(0) to WR_REQ_GLC(1)
   $display("axil_driver: address");         // 120ns

    // # 900;    // What if...?
   @(posedge axil_ifc.clk);
   axil_ifc.awaddr  = AxilDriver_write_addr;
   axil_ifc.awvalid = 1'b1;
   // for (int i = 0; i < 100; i++) begin
   // FIXME?? seems like this should happen BEFORE setting awvalid etc. above
   for (int i = 0; i < 10; i++) begin
      $display("Waiting for awready, i=%0d", i);  // 121-129ns
      if (axil_ifc.awready == 1) break;
      @(posedge axil_ifc.clk);
      if (i == 9) $display("axi slave is not ready 1");
   end
   @(posedge axil_ifc.clk);
   axil_ifc.awvalid = 1'b0;
   @(posedge axil_ifc.clk);
   // Axi controller should now be in state 1 (WR_REQ_GLC)  //132ns

   // glc_axi_ctrl.sv
   // typedef enum logic[2:0] {
   //     WR_IDLE = 3'h0,
   //     WR_REQ_GLC = 3'h1,
   //     WR_REQ_GLB = 3'h2,
   //     WR_WAIT = 3'h3,
   //     WR_RESP = 3'h4
   // } WrState;

   ////////////////////////////////////////////////////////////////////////
   // @(vif.cbd);
   // this.vif.cbd.wdata  <= data;
   // this.vif.cbd.wvalid <= 1'b1;
   // for (int i = 0; i < 100; i++) begin
   //    if (this.vif.cbd.wready == 1) break;
   //    @(vif.cbd);
   //     if (i == 99) return;  // axi slave is not ready
   // end
   // @(vif.cbd);
   // this.vif.cbd.wvalid <= 0;

   // Axi controller should now be in state 1 (WR_REQ_GLC)  // 132ns
   $display("axil_driver: data");  // ~132ns
   axil_ifc.wdata  = AxilDriver_write_data;
   axil_ifc.wvalid = 1'b1;
   // Axi controller should now be in state 3 (WR_WAIT)  // 132ns
   // Then, after one cycle, on to state 4 (WR_RESP)     // 133ns
   // where it stays until wr_wait_cnt counts from clog2(14) down to zero
   // Then back to IDLE maybe (state 0)
   // for (int i = 0; i < 100; i++) begin
   for (int i = 0; i < 20; i++) begin
      if (axil_ifc.wready == 1) break;
      @(posedge axil_ifc.clk);
      // if (i == 99) $display("axi slave is not ready 2");  // ~224ns
      if (i == 19) $display("axi slave is not ready 2");     // ~152ns
   end
   @(posedge axil_ifc.clk);
   axil_ifc.wvalid = 1'b0;
   // Axi controller should now be in state 0 (WR_IDLE)   // 153ns

   ////////////////////////////////////////////////////////////////////////
   // this.vif.cbd.bready <= 1'b1;
   // for (int i = 0; i < 100; i++) begin
   //     if (this.vif.cbd.bvalid == 1) break;
   //     @(vif.cbd);
   //     if (i == 99) return;  // axi slave is not ready
   // end
   // @(vif.cbd);
   // this.vif.cbd.bready <= 0;
   // @(vif.cbd);
   // axil_lock.put(1);

   // Releasing the bus I guess.
   axil_ifc.bready = 1'b1;    // 153ns
   //for (int i = 0; i < 100; i++) begin
   for (int i = 0; i < 10; i++) begin
      if (axil_ifc.bvalid == 1) break;
      @(posedge axil_ifc.clk);
      // if (i == 99) $display("axi slave is not ready 3");
      if (i == 9) $display("axi slave is not ready 3");
   end
   @(posedge axil_ifc.clk);
   axil_ifc.bready = 0;   // 164ns
   @(posedge axil_ifc.clk);
   axil_lock.put(1);

endtask


// task AxilDriver::read(bit [CGRA_AXI_ADDR_WIDTH-1:0]     addr,
//                       ref bit [CGRA_AXI_DATA_WIDTH-1:0] data);
bit [CGRA_AXI_ADDR_WIDTH-1:0] AxilDriver_read_addr;
bit [CGRA_AXI_DATA_WIDTH-1:0] AxilDriver_read_data;
task AxilDriver_read();
    $display("AxilDriver_read() wants the lock"); $fflush();
    axil_lock.get(1);
    $display("AxilDriver_read() got the lock"); $fflush();

    @(posedge axil_ifc.clk);
    axil_ifc.araddr  = AxilDriver_read_addr;
    axil_ifc.arvalid = 1'b1;
    axil_ifc.rready  = 1;
    for (int i = 0; i < 10; i++) begin
        if (axil_ifc.arready == 1) break;
        @(posedge axil_ifc.clk);
        // if (i == 9) return;  // axi slave is not ready
        if (i == 9) $display("axi slave is not ready 1");
    end
    @(posedge axil_ifc.clk);
    axil_ifc.arvalid = 0;
    @(posedge axil_ifc.clk);
    for (int i = 0; i < 10; i++) begin
        if (axil_ifc.rvalid == 1) break;
        @(posedge axil_ifc.clk);
        // if (i == 9) return;  // axi slave is not ready
        if (i == 9) $display("axi slave is not ready 2");
    end
    AxilDriver_read_data = axil_ifc.rdata;
    @(posedge axil_ifc.clk);
    axil_ifc.rready = 0;
    @(posedge axil_ifc.clk);
    $display("[%0t] AXI-Lite Read. Addr: %08h, Data: %08h", 
             $time, AxilDriver_read_addr, AxilDriver_read_data);
    $display("AxilDriver_read() releasing the lock"); $fflush();
    axil_lock.put(1);
    $display("AxilDriver_read() released the lock"); $fflush();
endtask
