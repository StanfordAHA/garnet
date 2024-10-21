   task axil_drive_write();

      ////////////////////////////////////////////////////////////////////////
      // $display("AXI-Lite Write. Addr: %08h, Data: %08h", addr, data);
      // axil_lock.get(1);

      $display("AXI-Lite Write. Addr: %08h, Data: %08h", addr, data);

      // semaphore axil_lock;
      $display("axil_driver: Gettum lockum"); $fflush();
      axil_lock.get(1);
      $display("axil_driver: Gottum lockum"); $fflush();

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

      $display("axil_driver: address");
      @(posedge axil_ifc.clk);
      axil_ifc.awaddr  = addr;
      axil_ifc.awvalid = 1'b1;
      for (int i = 0; i < 100; i++) begin
         if (axil_ifc.awready == 1) break;
         @(posedge axil_ifc.clk);
         if (i == 99) $display("axi slave is not ready");
      end
      @(posedge axil_ifc.clk);
      axil_ifc.awvalid = 1'b0;

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

      $display("axil_driver: data");
      @(posedge axil_ifc.clk);
      axil_ifc.wdata  = data;
      axil_ifc.wvalid = 1'b1;
      for (int i = 0; i < 100; i++) begin
         if (axil_ifc.wready == 1) break;
         @(posedge axil_ifc.clk);
         if (i == 99) $display("axi slave is not ready");
      end
      @(posedge axil_ifc.clk);
      axil_ifc.wvalid = 1'b0;














   endtask
