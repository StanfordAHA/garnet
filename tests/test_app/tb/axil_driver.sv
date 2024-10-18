class AxilDriver;
    vAxilIfcDriver vif;
    semaphore axil_lock;

    extern function new(vAxilIfcDriver vif, semaphore axil_lock);
    extern task config_write(Config cfg[]);
    extern task write(bit [CGRA_AXI_ADDR_WIDTH-1:0] addr, bit [CGRA_AXI_DATA_WIDTH-1:0] data);
    extern task read(bit [CGRA_AXI_ADDR_WIDTH-1:0] addr,
                     ref bit [CGRA_AXI_DATA_WIDTH-1:0] data);
endclass

// function AxilDriver::new(vAxilIfcDriver vif, semaphore axil_lock);
function AxilDriver::new(vAxilIfc vif, semaphore axil_lock);
    this.vif = vif;
    this.axil_lock = axil_lock;
endfunction

task AxilDriver::config_write(Config cfg[]);
    foreach (cfg[i]) begin
        write(cfg[i].addr, cfg[i].data);
    end
endtask

task AxilDriver::write(bit [CGRA_AXI_ADDR_WIDTH-1:0] addr, bit [CGRA_AXI_DATA_WIDTH-1:0] data);
    // $display("AXI-Lite Write. Addr: %08h, Data: %08h", addr, data);
    $display("AXI-Lite Write. Addr: %08h, Data: %08h", addr, data);
    $display("axil_driver: Gettum lockum"); $fflush();
    axil_lock.get(1);
    $display("axil_driver: Gottum lockum"); $fflush();

    $display("axil_driver 32: i see vif.wvalid = %0d", vif.wvalid); $fflush();

    @(posedge vif.clk);                 // WAS CLOCKING @(vif.cbd)
    vif.awaddr  <= addr;                // WAS CLOCKING vif.cbd.<>
    vif.awvalid <= 1'b1;                // WAS CLOCKING vif.cbd<>
    for (int i = 0; i < 100; i++) begin
        if (vif.awready == 1) break;    // WAS CLOCKING vif.cbd<>
        @(posedge vif.clk);             // WAS CLOCKING @(vif.cbd)
        if (i == 99) return;  // axi slave is not ready
    end







    @(posedge vif.clk);                 // WAS CLOCKING @(vif.cbd)
    vif.wvalid = 1'b0;                // WAS CLOCKING vif.cbd<>
    @(posedge vif.clk);                 // WAS CLOCKING @(vif.cbd)
   $display("axil_driver 36: i see vif.wvalid = %0d (should be 0)", vif.wvalid); $fflush();

    vif.wvalid = 1'b1;                // WAS CLOCKING vif.cbd<>
    // vif.driver.wvalid = 1'b1;  // MemberSel of non-variable
    @(posedge vif.clk);                 // WAS CLOCKING @(vif.cbd)
   $display("axil_driver 39: i see vif.wvalid = %0d (should be 1)", vif.wvalid); $fflush();

    repeat (20) @(posedge vif.clk);
   $finish(0);
endtask

task AxilDriver::read(bit [CGRA_AXI_ADDR_WIDTH-1:0] addr,
                      ref bit [CGRA_AXI_DATA_WIDTH-1:0] data);
    axil_lock.get(1);
    axil_lock.put(1);
endtask

