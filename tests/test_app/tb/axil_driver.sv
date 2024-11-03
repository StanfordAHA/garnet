class AxilDriver;
    vAxilIfcDriver vif;
    semaphore axil_lock;

    extern function new(vAxilIfcDriver vif, semaphore axil_lock);
    extern task config_write(Config cfg[]);
    extern task write(bit [CGRA_AXI_ADDR_WIDTH-1:0] addr, bit [CGRA_AXI_DATA_WIDTH-1:0] data);
    extern task read(bit [CGRA_AXI_ADDR_WIDTH-1:0] addr,
                     ref bit [CGRA_AXI_DATA_WIDTH-1:0] data);
endclass

function AxilDriver::new(vAxilIfcDriver vif, semaphore axil_lock);
    this.vif = vif;
    this.axil_lock = axil_lock;
endfunction

task AxilDriver::config_write(Config cfg[]);
    foreach (cfg[i]) begin
        write(cfg[i].addr, cfg[i].data);
    end
endtask

task AxilDriver::write(bit [CGRA_AXI_ADDR_WIDTH-1:0] addr, bit [CGRA_AXI_DATA_WIDTH-1:0] data);
    $display("AXI-Lite Write. Addr: %08h, Data: %08h", addr, data);
    axil_lock.get(1);
    @(posedge vif.clk);  // added to match non-clocking timing...

    @(posedge vif.clk);  // @(vif.cbd);
    vif.awaddr  <= addr;
    vif.awvalid <= 1'b1;
    for (int i = 0; i < 100; i++) begin
        if (vif.awready == 1) break;
        @(posedge vif.clk);  // @(vif.cbd);
        if (i == 99) return;  // axi slave is not ready
    end
    @(posedge vif.clk);  // @(vif.cbd);
    vif.awvalid <= 0;
    @(posedge vif.clk);  // @(vif.cbd);
    this.vif.wdata  <= data;
    this.vif.wvalid <= 1'b1;
    for (int i = 0; i < 100; i++) begin
        if (this.vif.wready == 1) break;
        @(posedge vif.clk);  // @(vif.cbd);
        if (i == 99) return;  // axi slave is not ready
    end
    @(posedge vif.clk);  // @(vif.cbd);
    this.vif.wvalid <= 0;
    this.vif.bready <= 1'b1;
    for (int i = 0; i < 100; i++) begin
        if (this.vif.bvalid == 1) break;
        @(posedge vif.clk);  // @(vif.cbd);
        if (i == 99) return;  // axi slave is not ready
    end
    @(posedge vif.clk);  // @(vif.cbd);
    this.vif.bready <= 0;
    @(posedge vif.clk);  // @(vif.cbd);
    axil_lock.put(1);
endtask

task AxilDriver::read(bit [CGRA_AXI_ADDR_WIDTH-1:0] addr,
                      ref bit [CGRA_AXI_DATA_WIDTH-1:0] data);
    axil_lock.get(1);
    @(posedge vif.clk);  // added to match non-clocking timing...

    @(posedge vif.clk);  // @(vif.cbd);
    this.vif.araddr  <= addr;
    this.vif.arvalid <= 1'b1;
    this.vif.rready  <= 1;
    for (int i = 0; i < 100; i++) begin
        if (this.vif.arready == 1) break;
        @(posedge vif.clk);  // @(vif.cbd);
        if (i == 99) return;  // axi slave is not ready
    end
    @(posedge vif.clk);  // @(vif.cbd);
    this.vif.arvalid <= 0;
    @(posedge vif.clk);  // @(vif.cbd);
    for (int i = 0; i < 100; i++) begin
        if (this.vif.rvalid == 1) break;
        @(posedge vif.clk);  // @(vif.cbd);
        if (i == 99) return;  // axi slave is not ready
    end
    data = this.vif.rdata;
    @(posedge vif.clk);  // @(vif.cbd);
    this.vif.rready <= 0;
    @(posedge vif.clk);  // @(vif.cbd);
    $display("AXI-Lite Read. Addr: %08h, Data: %08h", addr, data);
    axil_lock.put(1);
endtask

